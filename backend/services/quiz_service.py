"""Quiz generation and answering business logic."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from models.quiz import QuizQuestion, QuizAttempt
from models.document_structure import DocumentStructure
from models.document import Document as DocumentModel
from services.ai_knowledge_processor import _clean_json_response, _safe_json_loads
from services.prompts import QUIZ_GENERATION_PROMPT
from services.progress_service import ProgressService

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(self, db):
        self.db = db

    async def generate_quizzes(self, ai_service, document_id: str, ai_model_label: str, force: bool = False) -> int:
        """Generate quiz questions from a document's knowledge points."""
        # Check existing questions
        existing_count = self.db.query(QuizQuestion).filter(
            QuizQuestion.document_id == document_id
        ).count()
        if existing_count > 0 and not force:
            return existing_count

        # If force, delete old questions and attempts
        if force:
            old_questions = self.db.query(QuizQuestion).filter(
                QuizQuestion.document_id == document_id
            ).all()
            for q in old_questions:
                self.db.query(QuizAttempt).filter(QuizAttempt.quiz_question_id == q.id).delete()
                self.db.delete(q)
            self.db.flush()

        # Get document info for context
        doc = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        doc_title = doc.filename if doc else "未知文档"
        subject = self._infer_subject(doc_title)

        # Read knowledge points from DocumentStructure
        structure = self.db.query(DocumentStructure).filter(
            DocumentStructure.document_id == document_id
        ).first()
        if not structure or not structure.knowledge_points_json:
            return 0

        try:
            all_points = json.loads(structure.knowledge_points_json)
        except (json.JSONDecodeError, ValueError):
            return 0

        # Filter knowledge points - exclude low-value types and garbage text
        import re as _re
        skip_types = {"example"}
        filtered = []
        for p in all_points:
            if not isinstance(p, dict) or p.get("type") in skip_types:
                continue
            text = str(p.get("text", "")).strip()
            if len(text) < 6:
                continue
            # Skip unit/page references like "UNIT 5 WORKING THE LAND 59"
            if _re.match(r'^UNIT\s+\d+\s+.*\d+$', text, _re.IGNORECASE):
                continue
            # Skip pure page number references
            if _re.match(r'^p\.\s*\d+', text) or _re.match(r'^\d+$', text.strip()):
                continue
            # Skip very short fragments with mostly numbers
            if len(text) < 20 and sum(c.isdigit() for c in text) > len(text) * 0.4:
                continue
            filtered.append(p)

        if not filtered:
            logger.info(f"No filtered points for doc {document_id}")
            return 0

        logger.info(f"Generating quizzes for doc {document_id}: {len(filtered)} points in {((len(filtered)-1)//8)+1} batches")

        # Batch processing (8-10 points per batch)
        batch_size = 8
        total_generated = 0

        for i in range(0, len(filtered), batch_size):
            batch = filtered[i:i + batch_size]
            batch_text = json.dumps(batch, ensure_ascii=False, indent=2)

            prompt = QUIZ_GENERATION_PROMPT.replace("{document_title}", doc_title).replace("{subject}", subject).replace("{knowledge_points}", batch_text)

            try:
                response = await ai_service.chat_completion(prompt, stream=False)
                if isinstance(response, dict) and "response" in response:
                    raw = response["response"]
                else:
                    raw = str(response)

                logger.info(f"Batch {i//batch_size+1}: AI response length={len(raw)}, preview={raw[:200]}")

                cleaned = _clean_json_response(raw)
                quizzes = _safe_json_loads(cleaned)

                if not isinstance(quizzes, list):
                    logger.warning(f"Batch {i//batch_size+1}: parsed result is not a list: {type(quizzes)}, cleaned={cleaned[:200]}")
                    continue

                for q in quizzes:
                    if not isinstance(q, dict) or "question" not in q or "options" not in q:
                        continue
                    options = q.get("options", [])
                    if not isinstance(options, list) or len(options) != 4:
                        continue

                    # Skip meta-information questions (no learning value)
                    q_text = q.get("question", "")
                    if self._is_meta_question(q_text, options):
                        logger.info(f"Skipped meta question: {q_text[:60]}")
                        continue

                    # Find matching knowledge point text
                    kp_text = ""
                    for p in batch:
                        p_summary = p.get("summary", "") or p.get("text", "")
                        if p_summary and (p_summary[:50] in q.get("question", "") or any(p_summary[:30] in opt for opt in options)):
                            kp_text = p.get("text", "")[:200]
                            break

                    question = QuizQuestion(
                        document_id=document_id,
                        knowledge_point_text=kp_text or batch[0].get("text", "")[:200] if batch else "",
                        question_text=q.get("question", ""),
                        options_json=json.dumps(options, ensure_ascii=False),
                        correct_index=max(0, min(3, int(q.get("correct_index", 0)))),
                        explanation=q.get("explanation", ""),
                        difficulty=q.get("difficulty", "medium"),
                        ai_model=ai_model_label,
                    )
                    self.db.add(question)
                    total_generated += 1

                self.db.flush()

            except Exception as e:
                logger.warning(f"Quiz generation batch {i//batch_size+1} failed: {e}", exc_info=True)
                continue

        self.db.commit()
        logger.info(f"Quiz generation done for doc {document_id}: {total_generated} questions")
        return total_generated

    def get_documents_with_quizzes(self, user_id: str) -> List[Dict]:
        """Return documents that have quiz questions, with stats."""
        from sqlalchemy import func as sa_func

        # Get distinct document_ids from quiz_questions
        doc_ids = self.db.query(QuizQuestion.document_id).distinct().all()
        doc_ids = [d[0] for d in doc_ids]

        result = []
        for doc_id in doc_ids:
            doc = self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not doc:
                continue

            total = self.db.query(QuizQuestion).filter(
                QuizQuestion.document_id == doc_id
            ).count()

            answered = self.db.query(QuizAttempt).join(
                QuizQuestion, QuizAttempt.quiz_question_id == QuizQuestion.id
            ).filter(
                QuizAttempt.user_id == user_id,
                QuizQuestion.document_id == doc_id,
            ).count()

            correct = self.db.query(QuizAttempt).join(
                QuizQuestion, QuizAttempt.quiz_question_id == QuizQuestion.id
            ).filter(
                QuizAttempt.user_id == user_id,
                QuizQuestion.document_id == doc_id,
                QuizAttempt.is_correct == True,
            ).count()

            result.append({
                "document_id": doc_id,
                "filename": doc.filename,
                "total_questions": total,
                "answered": answered,
                "correct": correct,
            })

        return result

    def get_quizzes_by_document(self, document_id: str, user_id: str) -> List[Dict]:
        """Get all quiz questions for a document, with user's attempts."""
        questions = self.db.query(QuizQuestion).filter(
            QuizQuestion.document_id == document_id
        ).order_by(QuizQuestion.id).all()

        result = []
        for q in questions:
            attempt = self.db.query(QuizAttempt).filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_question_id == q.id,
            ).first()

            result.append({
                "id": q.id,
                "question_text": q.question_text,
                "options": json.loads(q.options_json) if q.options_json else [],
                "difficulty": q.difficulty,
                "knowledge_point_text": q.knowledge_point_text,
                "attempt": {
                    "selected_index": attempt.selected_index,
                    "is_correct": attempt.is_correct,
                } if attempt else None,
            })

        return result

    def submit_answer(self, user_id: str, quiz_question_id: int, selected_index: int) -> Dict:
        """Record a quiz attempt and update mastery."""
        question = self.db.query(QuizQuestion).filter(QuizQuestion.id == quiz_question_id).first()
        if not question:
            return {"error": "题目不存在"}

        # Check if already answered
        existing = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.quiz_question_id == quiz_question_id,
        ).first()
        if existing:
            return {
                "is_correct": existing.is_correct,
                "correct_index": question.correct_index,
                "explanation": question.explanation,
                "already_answered": True,
            }

        is_correct = selected_index == question.correct_index
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_question_id=quiz_question_id,
            selected_index=selected_index,
            is_correct=is_correct,
        )
        self.db.add(attempt)
        self.db.flush()

        # Update knowledge mastery
        if question.knowledge_point_text:
            try:
                progress_svc = ProgressService(self.db)
                delta = 0.15 if is_correct else 0.05
                progress_svc.update_knowledge_mastery(
                    user_id, question.document_id,
                    question.knowledge_point_text, delta
                )
            except Exception as e:
                logger.warning(f"Failed to update mastery: {e}")

        self.db.commit()

        return {
            "is_correct": is_correct,
            "correct_index": question.correct_index,
            "explanation": question.explanation,
        }

    def get_quiz_stats(self, user_id: str, document_id: str) -> Dict:
        """Get quiz statistics for a document."""
        total = self.db.query(QuizQuestion).filter(
            QuizQuestion.document_id == document_id
        ).count()

        answered = self.db.query(QuizAttempt).join(
            QuizQuestion, QuizAttempt.quiz_question_id == QuizQuestion.id
        ).filter(
            QuizAttempt.user_id == user_id,
            QuizQuestion.document_id == document_id,
        ).count()

        correct = self.db.query(QuizAttempt).join(
            QuizQuestion, QuizAttempt.quiz_question_id == QuizQuestion.id
        ).filter(
            QuizAttempt.user_id == user_id,
            QuizQuestion.document_id == document_id,
            QuizAttempt.is_correct == True,
        ).count()

        return {
            "total": total,
            "answered": answered,
            "correct": correct,
            "accuracy": round(correct / answered * 100, 1) if answered > 0 else 0,
        }

    @staticmethod
    def _is_meta_question(question: str, options: list) -> bool:
        """Detect meta-information questions that have no learning value."""
        import re as _re
        # Patterns that indicate document-structure / metadata questions
        meta_patterns = [
            r'出自.*哪', r'哪个.*出版', r'出版社', r'哪个.*章节', r'哪个.*单元',
            r'针对.*学科', r'属于.*册', r'哪本.*书', r'资料.*针对',
            r'本习题', r'本文档', r'本书.*主要', r'哪一册',
        ]
        q_lower = question.lower()
        for pat in meta_patterns:
            if _re.search(pat, q_lower):
                return True
        # Also check if options contain publisher names or book titles
        opt_text = ' '.join(str(o) for o in options)
        if _re.search(r'出版社|必修.*第.*册|选修.*第.*册', opt_text):
            return True
        return False

    @staticmethod
    def _infer_subject(filename: str) -> str:
        """Infer the subject area from the document filename."""
        fn = filename.lower()
        if "数学" in fn or "math" in fn:
            return "数学"
        if "英语" in fn or "english" in fn or "英文" in fn:
            return "英语"
        if "语文" in fn or "chinese" in fn or "文学" in fn:
            return "语文"
        if "化学" in fn or "chemistry" in fn:
            return "化学"
        if "物理" in fn or "physics" in fn:
            return "物理"
        if "生物" in fn or "biology" in fn or "生命" in fn:
            return "生物"
        if "地理" in fn or "geography" in fn or "自然地理" in fn:
            return "地理"
        if "历史" in fn or "history" in fn:
            return "历史"
        if "政治" in fn or "道法" in fn or "道德" in fn:
            return "政治/道德与法治"
        if "统计" in fn or "数据分析" in fn or "社会" in fn:
            return "统计学/社会科学"
        return "综合学科"
