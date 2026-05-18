"""Quiz models - stores generated quiz questions and user attempts."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from core.database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    knowledge_point_text = Column(String(200), nullable=True)
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    correct_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")
    ai_model = Column(String(100), nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    quiz_question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    selected_index = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
