from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(String, default="")  # Stored as YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("CallSessionRecord", back_populates="user", cascade="all, delete-orphan")


class CallSessionRecord(Base):
    __tablename__ = "call_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    persona_id = Column(String, nullable=True)
    persona_name = Column(String, nullable=False)
    persona_role = Column(String, nullable=False)
    persona_company = Column(String, nullable=False)
    difficulty_level = Column(String, default="Hard")
    overall_score = Column(Integer, default=0)
    outcome_label = Column(String, default="Completed")
    talk_ratio_user_pct = Column(Float, default=50.0)
    talk_ratio_buyer_pct = Column(Float, default=50.0)
    questions_asked = Column(Integer, default=0)
    interruptions_count = Column(Integer, default=0)
    buzzwords_json = Column(Text, default="[]")
    coaching_summary = Column(Text, default="")
    re_pitch_prompt = Column(Text, default="")
    peak_moment_json = Column(Text, default="")
    fatal_moment_json = Column(Text, default="")
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
