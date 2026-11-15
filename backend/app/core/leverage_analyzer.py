import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_groq import ChatGroq
from backend.app.config import settings

logger = logging.getLogger("verbalpause.leverage")


class TurningPoint(BaseModel):
    timestamp_sec: float
    point_type: str  # "peak_gain" | "fatal_drop"
    speaker: str
    quote: str
    leverage_score: float
    analysis: str
    suggested_re_pitch: str


class CallScorecard(BaseModel):
    overall_score: int  # 0 to 100
    outcome_label: str
    talk_ratio_user_pct: float
    talk_ratio_buyer_pct: float
    questions_asked: int
    buzzwords_used: List[str]
    interruptions_count: int
    peak_moment: Optional[TurningPoint] = None
    fatal_drop_moment: Optional[TurningPoint] = None
    turning_points: List[TurningPoint]
    coaching_summary: str
    re_pitch_sandbox_prompt: str


class LeverageAnalyzer:
    """Analyzes negotiation dynamics and pinpoints the exact seconds leverage was won or lost."""

    def __init__(self):
        llm_kwargs = {
            "model": settings.default_model,
            "temperature": 0.2,
            "max_tokens": 2500,
            "groq_api_key": settings.groq_api_key
        }
        try:
            self.llm = ChatGroq(**llm_kwargs, reasoning_effort="low")
        except Exception:
            self.llm = ChatGroq(**llm_kwargs)

    async def analyze_call(
        self,
        persona_name: str,
        persona_role: str,
        conversation_turns: List[Dict[str, str]],
        state_summary: Dict[str, Any]
    ) -> CallScorecard:
        """Evaluates the full dialogue and outputs turning points, leverage curve, and re-pitch coaching."""
        user_turns = [t for t in conversation_turns if t.get("role") == "user" and t.get("content", "").strip()]
        opening_prompt = conversation_turns[0].get("content") if conversation_turns else "What is this regarding?"

        # Edge Case 1: Empty call (user started session and immediately clicked End Call without answering)
        if not user_turns:
            return CallScorecard(
                overall_score=0,
                outcome_label="Call Aborted (No Response Provided)",
                talk_ratio_user_pct=0.0,
                talk_ratio_buyer_pct=100.0,
                questions_asked=0,
                buzzwords_used=[],
                interruptions_count=0,
                peak_moment=None,
                fatal_drop_moment=None,
                turning_points=[],
                coaching_summary="The session was ended immediately without any verbal response from the candidate. Speak into your microphone or submit a pitch in the input bar to practice handling buyer objections and earn a negotiation score.",
                re_pitch_sandbox_prompt=opening_prompt
            )

        # Edge Case 2: Incomplete drop-off (user spoke once with only a name or 1-5 words and ended call)
        user_total_words = sum(len(t.get("content", "").split()) for t in user_turns)
        if len(user_turns) == 1 and user_total_words <= 6:
            single_quote = user_turns[0].get("content", "")
            drop_moment = TurningPoint(
                timestamp_sec=float(user_turns[0].get("timestamp_sec", 2.0)),
                point_type="fatal_drop",
                speaker="user",
                quote=single_quote,
                leverage_score=-2.5,
                analysis="The candidate introduced themselves but disconnected before delivering a value proposition or answering the buyer's 3-minute constraint.",
                suggested_re_pitch=f"Thanks for taking my call, {persona_name}. I know you have a hard stop in 3 minutes—I'm reaching out because teams like yours are dealing with unexpected downtime. Do you have 60 seconds to see how we solve that?"
            )
            return CallScorecard(
                overall_score=15,
                outcome_label="Call Dropped (Incomplete Introduction)",
                talk_ratio_user_pct=10.0,
                talk_ratio_buyer_pct=90.0,
                questions_asked=0,
                buzzwords_used=[],
                interruptions_count=0,
                peak_moment=None,
                fatal_drop_moment=drop_moment,
                turning_points=[drop_moment],
                coaching_summary="The call was disconnected after an initial introduction before pitching any value. In enterprise negotiations, the opening 20 seconds must immediately justify why the buyer should stay on the line.",
                re_pitch_sandbox_prompt=opening_prompt
            )

        # Active call analysis
        calculated_score = state_summary.get("overall_score", 50)
        calculated_outcome = state_summary.get("outcome", "Practice Completed")

        formatted_dialogue = "\n".join(
            f"[{t.get('role', 'Speaker').upper()}]: {t.get('content', '')}"
            for t in conversation_turns
        )

        prompt = f"""You are a master executive sales negotiation coach reviewing an adversarial roleplay simulation.

Buyer Persona: {persona_name} ({persona_role})
Roleplay Dialogue Transcript:
{formatted_dialogue}

Telemetry Summary:
- Ground-Truth Calculated Score: {calculated_score} / 100
- Outcome Category: {calculated_outcome}
- Interruptions Triggered: {state_summary.get('interruptions_triggered', 0)}
- Buzzwords Detected: {state_summary.get('buzzwords_used', [])}
- Questions Asked by User: {state_summary.get('questions_asked', 0)}

Analyze the conversation and return a valid JSON object (pure JSON, no markdown) with the following structure:
{{
  "overall_score": {calculated_score},
  "outcome_label": "{calculated_outcome}",
  "coaching_summary": "3-sentence executive diagnosis of candidate's negotiation strengths and fatal blunders.",
  "turning_points": [
    {{
      "timestamp_sec": 18.0,
      "point_type": "peak_gain",
      "speaker": "user",
      "quote": "Exact sentence from user that earned credibility",
      "leverage_score": 4.5,
      "analysis": "Why this moved leverage in the candidate's favor.",
      "suggested_re_pitch": "Alternative even stronger phrasing."
    }},
    {{
      "timestamp_sec": 42.0,
      "point_type": "fatal_drop",
      "speaker": "user",
      "quote": "Exact sentence where candidate panicked, caved, or monologued",
      "leverage_score": -3.2,
      "analysis": "Exact behavioral failure (e.g. offered premature discount, answered unasked objection).",
      "suggested_re_pitch": "The exact masterclass counter-objection response they should have used instead."
    }}
  ],
  "re_pitch_sandbox_prompt": "The single toughest objection from the buyer that the user must re-record to salvage the deal."
}}
"""
        response = self.llm.invoke(prompt)
        raw_text = response.content.strip()

        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(raw_text)
        except Exception:
            data = {
                "overall_score": state_summary.get("overall_score", 70),
                "outcome_label": state_summary.get("outcome", "Practice Completed"),
                "coaching_summary": "Session finished. Candidate showed solid technical domain knowledge with room for tighter objection handling.",
                "turning_points": [],
                "re_pitch_sandbox_prompt": "How does your pricing compare to in-house engineering costs?"
            }

        points = []
        for pt in data.get("turning_points", []):
            points.append(
                TurningPoint(
                    timestamp_sec=float(pt.get("timestamp_sec", 10.0)),
                    point_type=pt.get("point_type", "fatal_drop"),
                    speaker=pt.get("speaker", "user"),
                    quote=pt.get("quote", "Transcript excerpt"),
                    leverage_score=float(pt.get("leverage_score", 0.0)),
                    analysis=pt.get("analysis", "Turn analysis"),
                    suggested_re_pitch=pt.get("suggested_re_pitch", "Try isolating the objection first.")
                )
            )

        peak = next((p for p in points if p.point_type == "peak_gain"), None)
        fatal = next((p for p in points if p.point_type == "fatal_drop"), None)

        talk_ratio_str = state_summary.get("talk_to_listen_ratio", "50% User / 50% Buyer")
        try:
            user_pct = float(talk_ratio_str.split("%")[0])
        except Exception:
            user_pct = 50.0

        final_score = calculated_score
        if "overall_score" in data and isinstance(data["overall_score"], (int, float)):
            llm_val = int(data["overall_score"])
            if abs(llm_val - calculated_score) <= 4:
                final_score = llm_val

        return CallScorecard(
            overall_score=final_score,
            outcome_label=calculated_outcome,
            talk_ratio_user_pct=user_pct,
            talk_ratio_buyer_pct=round(100.0 - user_pct, 1),
            questions_asked=state_summary.get("questions_asked", 0),
            buzzwords_used=state_summary.get("buzzwords_used", []),
            interruptions_count=state_summary.get("interruptions_triggered", 0),
            peak_moment=peak,
            fatal_drop_moment=fatal,
            turning_points=points,
            coaching_summary=data.get("coaching_summary", "Review complete."),
            re_pitch_sandbox_prompt=data.get("re_pitch_sandbox_prompt", "Defend your pricing against competitors.")
        )
