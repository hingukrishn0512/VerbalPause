import uuid
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.app.core.persona_generator import BuyerPersona, PRESET_PERSONAS
from backend.app.core.state_machine import NegotiationStateMachine
from backend.app.core.voice_agent import VoiceAgentRunner
from backend.app.core.leverage_analyzer import LeverageAnalyzer, CallScorecard

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])
leverage_analyzer = LeverageAnalyzer()

# Active in-memory session registry (can be backed by Redis in multi-instance setups)
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


class StartSessionRequest(BaseModel):
    persona_id: Optional[str] = None
    custom_persona: Optional[BuyerPersona] = None


class UserTurnRequest(BaseModel):
    transcript: str
    duration_sec: Optional[float] = 3.5


class RetryTurnRequest(BaseModel):
    objection_prompt: str
    candidate_new_response: str


@router.post("/start")
def start_simulation(payload: StartSessionRequest):
    """Initializes a new adversarial voice roleplay session with a chosen persona."""
    persona = None
    if payload.custom_persona:
        persona = payload.custom_persona
    elif payload.persona_id:
        persona = next((p for p in PRESET_PERSONAS if p.id == payload.persona_id), None)

    if not persona:
        persona = PRESET_PERSONAS[0]  # default to Marcus Vance (Skeptical VP of Eng)

    session_id = str(uuid.uuid4())
    state_machine = NegotiationStateMachine()
    agent_runner = VoiceAgentRunner(persona=persona, state_machine=state_machine)

    ACTIVE_SESSIONS[session_id] = {
        "session_id": session_id,
        "persona": persona,
        "state_machine": state_machine,
        "agent_runner": agent_runner,
        "turns": [],
        "created_at": time.time(),
        "is_ended": False,
        "scorecard": None,
    }

    # Opening buyer greeting
    opening_greeting = f"Hi, this is {persona.name}. I've only got about 3 or 4 minutes before my next sync—what's this regarding?"
    ACTIVE_SESSIONS[session_id]["turns"].append({
        "role": "buyer",
        "content": opening_greeting,
        "timestamp_sec": 0.0
    })

    return {
        "session_id": session_id,
        "persona": persona,
        "opening_greeting": opening_greeting,
        "initial_patience": state_machine.patience,
        "initial_skepticism": state_machine.skepticism,
        "initial_leverage": state_machine.deal_leverage,
    }


@router.post("/{session_id}/turn")
async def process_turn(session_id: str, payload: UserTurnRequest):
    """Processes a user speech turn, updates buyer emotion state, and returns response."""
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    if session["is_ended"]:
        raise HTTPException(status_code=400, detail="This session has already ended.")

    user_text = payload.transcript.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    t_sec = session["state_machine"].elapsed_seconds()
    session["turns"].append({
        "role": "user",
        "content": user_text,
        "timestamp_sec": t_sec
    })

    # Process through Voice Agent + State Machine
    runner: VoiceAgentRunner = session["agent_runner"]
    result = await runner.process_user_turn(
        user_transcript=user_text,
        duration_sec=payload.duration_sec or 3.5
    )

    session["turns"].append({
        "role": "buyer",
        "content": result["text"],
        "timestamp_sec": session["state_machine"].elapsed_seconds()
    })

    return {
        "session_id": session_id,
        "buyer_reply": result["text"],
        "is_interruption": result.get("is_interruption", False),
        "patience": result["patience"],
        "skepticism": result["skepticism"],
        "deal_leverage": result["deal_leverage"],
        "buzzwords_detected": result.get("buzzwords", []),
    }


@router.post("/{session_id}/end", response_model=CallScorecard)
async def end_simulation(session_id: str):
    """Ends the roleplay call and generates the post-call Leverage Waveform & Scorecard."""
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    session["is_ended"] = True
    sm: NegotiationStateMachine = session["state_machine"]
    persona: BuyerPersona = session["persona"]

    state_summary = sm.get_summary()

    scorecard = await leverage_analyzer.analyze_call(
        persona_name=persona.name,
        persona_role=f"{persona.role} at {persona.company}",
        conversation_turns=session["turns"],
        state_summary=state_summary
    )

    session["scorecard"] = scorecard
    return scorecard


@router.post("/{session_id}/retry-turn")
async def retry_objection_turn(session_id: str, payload: RetryTurnRequest):
    """
    1-Click Rewind & Re-Pitch Sandbox:
    Allows user to re-record a failed turn and see how the buyer responds to the better phrasing.
    """
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    persona: BuyerPersona = session["persona"]

    prompt = f"""You are roleplaying as {persona.name}, {persona.role} at {persona.company}.
{persona.system_prompt}

The candidate previously received this tough objection from you:
"{payload.objection_prompt}"

The candidate just re-tried with this new response:
"{payload.candidate_new_response}"

Evaluate the candidate's new response in 2-3 sentences:
1. Did they handle the objection effectively with proof/discovery, or are they still defensive?
2. How does your character react now? (Are you receptive to a POC, or still skeptical?)
3. Did their deal leverage recover? Give a score delta (-3 to +5).
"""
    runner: VoiceAgentRunner = session["agent_runner"]
    response = runner.llm.invoke(prompt)

    return {
        "buyer_reaction": response.content.strip(),
        "evaluated_response": payload.candidate_new_response
    }
