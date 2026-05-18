"""Progress tracking business logic."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models.learning_progress import LearningProgress
from models.knowledge_mastery import KnowledgeMastery
from models.study_session import StudySession
from models.document import Document as DocumentModel
from models.document_chunk import DocumentChunk
from models.quiz import QuizQuestion, QuizAttempt


class ProgressService:
    def __init__(self, db):
        self.db = db

    def get_or_create_progress(self, user_id: str, doc_id: str) -> LearningProgress:
        p = self.db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.document_id == doc_id,
        ).first()
        if not p:
            p = LearningProgress(user_id=user_id, document_id=doc_id, status="not_started")
            self.db.add(p)
            self.db.flush()
        return p

    def update_reading_progress(self, user_id: str, doc_id: str, chunk_index: int, time_seconds: int) -> LearningProgress:
        p = self.get_or_create_progress(user_id, doc_id)

        total = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
        p.time_spent_seconds = (p.time_spent_seconds or 0) + time_seconds
        p.last_chunk_index = max(p.last_chunk_index or 0, chunk_index)
        p.last_accessed_at = datetime.now()

        if total > 0:
            p.progress_percent = round(p.last_chunk_index / total * 100, 1)
        else:
            p.progress_percent = 0.0

        if p.progress_percent >= 100:
            p.status = "completed"
        else:
            p.status = "in_progress"

        self.db.commit()
        return p

    def update_knowledge_mastery(self, user_id: str, doc_id: str, point_text: str, delta: float = 0.1) -> KnowledgeMastery:
        text_key = point_text[:200]
        m = self.db.query(KnowledgeMastery).filter(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.document_id == doc_id,
            KnowledgeMastery.knowledge_point_text == text_key,
        ).first()

        if not m:
            m = KnowledgeMastery(
                user_id=user_id, document_id=doc_id,
                knowledge_point_text=text_key, mastery_level=0.0, review_count=0,
            )
            self.db.add(m)
            self.db.flush()

        m.mastery_level = min(1.0, max(0.0, (m.mastery_level or 0) + delta))
        m.review_count = (m.review_count or 0) + 1
        m.last_reviewed_at = datetime.now()
        self.db.commit()
        return m

    def start_study_session(self, user_id: str, doc_id: Optional[str], session_type: str) -> StudySession:
        import uuid
        s = StudySession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            document_id=doc_id,
            session_type=session_type,
            started_at=datetime.now(),
        )
        self.db.add(s)
        self.db.commit()
        return s

    def end_study_session(self, session_id: str) -> Optional[StudySession]:
        s = self.db.query(StudySession).filter(StudySession.id == session_id).first()
        if not s:
            return None
        s.ended_at = datetime.now()
        if s.started_at:
            s.duration_seconds = int((s.ended_at - s.started_at).total_seconds())
        self.db.commit()
        return s

    def get_user_dashboard(self, user_id: str) -> Dict:
        progresses = self.db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
        ).all()

        completed = sum(1 for p in progresses if p.status == "completed")

        # All sessions for this user
        all_sessions = self.db.query(StudySession).filter(
            StudySession.user_id == user_id,
        ).all()

        # Total time: sum of all completed study sessions
        total_time = sum(s.duration_seconds or 0 for s in all_sessions if s.duration_seconds)

        # Mastery summary
        masteries = self.db.query(KnowledgeMastery).filter(
            KnowledgeMastery.user_id == user_id,
        ).all()
        high = sum(1 for m in masteries if (m.mastery_level or 0) >= 0.7)
        medium = sum(1 for m in masteries if 0.3 <= (m.mastery_level or 0) < 0.7)
        low = sum(1 for m in masteries if (m.mastery_level or 0) < 0.3)

        # Recent sessions
        sessions = self.db.query(StudySession).filter(
            StudySession.user_id == user_id,
        ).order_by(StudySession.started_at.desc()).limit(10).all()

        # Daily stats - past 7 days
        daily_stats = []
        today = datetime.now().date()
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            day_sessions = [s for s in all_sessions
                           if s.started_at and day_start <= s.started_at <= day_end]
            day_seconds = sum(s.duration_seconds or 0 for s in day_sessions)
            daily_stats.append({
                "date": day.isoformat(),
                "minutes": round(day_seconds / 60, 1),
            })

        # Streak days
        streak_days = 0
        check_date = today
        session_dates = set()
        for s in all_sessions:
            if s.started_at:
                session_dates.add(s.started_at.date())
        while check_date in session_dates:
            streak_days += 1
            check_date -= timedelta(days=1)

        # Documents progress with filenames
        doc_progresses = []
        for p in progresses:
            doc = self.db.query(DocumentModel).filter(DocumentModel.id == p.document_id).first()
            doc_progresses.append({
                "document_id": p.document_id,
                "filename": doc.filename if doc else "已删除",
                "progress_percent": p.progress_percent or 0,
                "status": p.status,
                "time_spent_seconds": p.time_spent_seconds or 0,
                "last_accessed_at": p.last_accessed_at.isoformat() if p.last_accessed_at else None,
            })

        # Quiz stats - count all questions and attempts for this user
        total_quiz_questions = self.db.query(QuizQuestion).count()
        total_answered = self.db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).count()
        total_correct = self.db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id, QuizAttempt.is_correct == True
        ).count()

        return {
            "total_documents": len(progresses),
            "completed_documents": completed,
            "total_time_seconds": total_time,
            "documents_progress": doc_progresses,
            "mastery_summary": {"high": high, "medium": medium, "low": low},
            "total_knowledge_points": len(masteries),
            "streak_days": streak_days,
            "daily_stats": daily_stats,
            "recent_sessions": [
                {
                    "id": s.id, "document_id": s.document_id,
                    "session_type": s.session_type,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "duration_seconds": s.duration_seconds or 0,
                }
                for s in sessions
            ],
            "quiz_stats": {
                "total": total_quiz_questions,
                "answered": total_answered,
                "correct": total_correct,
            },
        }

    def get_document_progress(self, user_id: str, doc_id: str) -> Dict:
        p = self.get_or_create_progress(user_id, doc_id)
        total = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()

        masteries = self.db.query(KnowledgeMastery).filter(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.document_id == doc_id,
        ).all()

        return {
            "progress_percent": p.progress_percent or 0,
            "time_spent_seconds": p.time_spent_seconds or 0,
            "status": p.status,
            "last_chunk_index": p.last_chunk_index or 0,
            "chunks_total": total,
            "knowledge_mastery": [
                {
                    "text": m.knowledge_point_text,
                    "mastery_level": m.mastery_level or 0,
                    "review_count": m.review_count or 0,
                    "last_reviewed_at": m.last_reviewed_at.isoformat() if m.last_reviewed_at else None,
                }
                for m in masteries
            ],
        }
