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
        formatted_dialogue = "\n".join(
            f"[{t.get('role', 'Speaker').upper()}]: {t.get('content', '')}"
            for t in conversation_turns
        )

        prompt = f"""You are a master executive sales negotiation coach reviewing an adversarial roleplay simulation.

Buyer Persona: {persona_name} ({persona_role})
Roleplay Dialogue Transcript:
{formatted_dialogue}

Telemetry Summary:
- Interruptions Triggered: {state_summary.get('interruptions_triggered', 0)}
- Buzzwords Detected: {state_summary.get('buzzwords_used', [])}
- Questions Asked by User: {state_summary.get('questions_asked', 0)}

Analyze the conversation and return a valid JSON object (pure JSON, no markdown) with the following structure:
{{
  "overall_score": 74,
  "outcome_label": "High Conviction Next Steps / Stalled in Committee / Lost Deal",
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

        return CallScorecard(
            overall_score=data.get("overall_score", state_summary.get("overall_score", 70)),
            outcome_label=data.get("outcome_label", state_summary.get("outcome", "Completed")),
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
