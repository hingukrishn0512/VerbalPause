import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.database import get_db
from backend.app.db.models import User, CallSessionRecord
from backend.app.core.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


class DashboardStatsResponse(BaseModel):
    user_name: str
    current_streak: int
    longest_streak: int
    streak_status: str
    total_sessions: int
    average_score: float
    win_rate_pct: float
    avg_talk_ratio_user: float
    total_questions_asked: int
    total_interruptions: int
    top_improvement_area: str


class SessionListItem(BaseModel):
    id: str
    persona_name: str
    persona_role: str
    persona_company: str
    difficulty_level: str
    overall_score: int
    outcome_label: str
    duration_seconds: float
    questions_asked: int
    interruptions_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionListItem):
    talk_ratio_user_pct: float
    talk_ratio_buyer_pct: float
    buzzwords_used: List[str]
    coaching_summary: str
    re_pitch_prompt: str
    peak_moment: Optional[Dict[str, Any]] = None
    fatal_moment: Optional[Dict[str, Any]] = None


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculates aggregate negotiation KPIs and personalized AI coaching diagnoses."""
    # Sync streak if candidate missed practice days
    if current_user.last_active_date:
        try:
            last_date = datetime.strptime(current_user.last_active_date, "%Y-%m-%d").date()
            delta_days = (datetime.utcnow().date() - last_date).days
            if delta_days > 1 and current_user.current_streak > 0:
                current_user.current_streak = 0
                db.commit()
                db.refresh(current_user)
        except Exception:
            pass

    sessions = (
        db.query(CallSessionRecord)
        .filter(CallSessionRecord.user_id == current_user.id)
        .all()
    )

    total_sessions = len(sessions)
    if total_sessions == 0:
        streak_label = "🔥 Complete your first session to start your streak!" if current_user.current_streak == 0 else f"🔥 {current_user.current_streak}-Day Practice Streak! Keep your momentum going."
        return DashboardStatsResponse(
            user_name=current_user.full_name,
            current_streak=current_user.current_streak,
            longest_streak=current_user.longest_streak,
            streak_status=streak_label,
            total_sessions=0,
            average_score=0.0,
            win_rate_pct=0.0,
            avg_talk_ratio_user=0.0,
            total_questions_asked=0,
            total_interruptions=0,
            top_improvement_area="Complete your first roleplay call to generate your personal AI diagnostic.",
        )

    scores = [s.overall_score for s in sessions]
    avg_score = round(sum(scores) / total_sessions, 1)

    wins = sum(1 for s in sessions if "next steps" in s.outcome_label.lower() or s.overall_score >= 70)
    win_rate = round((wins / total_sessions) * 100, 1)

    avg_talk = round(sum(s.talk_ratio_user_pct for s in sessions) / total_sessions, 1)
    total_questions = sum(s.questions_asked for s in sessions)
    total_interruptions = sum(s.interruptions_count for s in sessions)

    # Diagnostic Rule-Based Improvement synthesis
    if total_interruptions / total_sessions >= 0.7:
        improvement = "High Monologue Frequency: You are getting interrupted in most calls. Force yourself to stop speaking every 12 seconds."
    elif total_questions / total_sessions < 1.0:
        improvement = "Passive Pitching: You are answering objections without qualifying the buyer. Aim for at least 2 open-ended discovery questions per call."
    elif avg_talk > 65.0:
        improvement = "Monopolizing Airtime: Your average talk time is over 65%. Shift to a 45/55 listen-first posture."
    elif avg_score < 50:
        improvement = "Value Hook Delivery: Calls are stalling early. Open with an immediate metric and acknowledge time constraints in the first 20 seconds."
    else:
        improvement = "Deal Leverage Mastery: Strong discovery posture and objection recovery. Focus on sealing formal POC timelines."

    streak_msg = f"🔥 {current_user.current_streak}-Day Practice Streak! Keep your momentum going."

    return DashboardStatsResponse(
        user_name=current_user.full_name,
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        streak_status=streak_msg,
        total_sessions=total_sessions,
        average_score=avg_score,
        win_rate_pct=win_rate,
        avg_talk_ratio_user=avg_talk,
        total_questions_asked=total_questions,
        total_interruptions=total_interruptions,
        top_improvement_area=improvement,
    )


@router.get("/sessions", response_model=List[SessionListItem])
def list_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves recent practice sessions for the logged-in candidate."""
    return (
        db.query(CallSessionRecord)
        .filter(CallSessionRecord.user_id == current_user.id)
        .order_by(CallSessionRecord.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches complete granular scorecard details for a past simulation."""
    rec = (
        db.query(CallSessionRecord)
        .filter(CallSessionRecord.id == session_id, CallSessionRecord.user_id == current_user.id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Session record not found.")

    buzzwords = []
    if rec.buzzwords_json:
        try:
            buzzwords = json.loads(rec.buzzwords_json)
        except Exception:
            pass

    peak = None
    if rec.peak_moment_json:
        try:
            peak = json.loads(rec.peak_moment_json)
        except Exception:
            pass

    fatal = None
    if rec.fatal_moment_json:
        try:
            fatal = json.loads(rec.fatal_moment_json)
        except Exception:
            pass

    return SessionDetailResponse(
        id=rec.id,
        persona_name=rec.persona_name,
        persona_role=rec.persona_role,
        persona_company=rec.persona_company,
        difficulty_level=rec.difficulty_level,
        overall_score=rec.overall_score,
        outcome_label=rec.outcome_label,
        duration_seconds=rec.duration_seconds,
        questions_asked=rec.questions_asked,
        interruptions_count=rec.interruptions_count,
        talk_ratio_user_pct=rec.talk_ratio_user_pct,
        talk_ratio_buyer_pct=rec.talk_ratio_buyer_pct,
        buzzwords_used=buzzwords,
        coaching_summary=rec.coaching_summary,
        re_pitch_prompt=rec.re_pitch_prompt,
        peak_moment=peak,
        fatal_moment=fatal,
        created_at=rec.created_at,
    )
