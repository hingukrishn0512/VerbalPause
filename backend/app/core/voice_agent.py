import time
import logging
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.app.config import settings
from backend.app.core.persona_generator import BuyerPersona
from backend.app.core.state_machine import NegotiationStateMachine

logger = logging.getLogger("verbalpause.agent")


class VoiceAgentRunner:
    """Orchestrates real-time adversarial buyer turns during a voice simulation."""

    def __init__(self, persona: BuyerPersona, state_machine: NegotiationStateMachine):
        self.persona = persona
        self.state_machine = state_machine
        self.llm = ChatGroq(
            model=settings.default_model,
            temperature=0.35,
            max_tokens=150,  # enforce short phone-call answers (1-3 sentences)
            groq_api_key=settings.groq_api_key
        )
        self.messages = [
            SystemMessage(content=persona.system_prompt)
        ]

    async def process_user_turn(self, user_transcript: str, duration_sec: float = 3.5) -> Dict[str, Any]:
        """
        Processes candidate's speech turn:
        1. Feeds input into the emotion state machine (calculates patience, skepticism, monologue check).
        2. If an active interruption is triggered, returns the interruption dialogue directly.
        3. Otherwise prompts the persona LLM to answer in character with concise friction.
        """
        # Run through state machine
        sm_result = self.state_machine.on_user_speech(user_transcript, duration_sec)

        # If buyer patience ran out and interruption triggered:
        if sm_result["should_interrupt"]:
            interrupt_text = sm_result["interrupt_dialogue"]
            self.messages.append(HumanMessage(content=user_transcript))
            self.messages.append(AIMessage(content=interrupt_text))
            self.state_machine.on_buyer_speech(interrupt_text, duration_sec=2.5, leverage_delta=-1.5, note="Buyer actively interrupted candidate.")
            return {
                "text": interrupt_text,
                "is_interruption": True,
                "patience": sm_result["patience"],
                "skepticism": sm_result["skepticism"],
                "deal_leverage": sm_result["deal_leverage"],
                "buzzwords": sm_result["buzzwords_found"],
            }

        # Context prompt enhancement with emotional state
        emotion_context = f"\n[Buyer State: Patience={sm_result['patience']}/100, Skepticism={sm_result['skepticism']}/100. Speak in 1-2 punchy sentences. Challenge the rep.]"
        
        self.messages.append(HumanMessage(content=user_transcript + emotion_context))

        t0 = time.perf_counter()
        response = self.llm.invoke(self.messages)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        buyer_text = response.content.strip()
        # Clean up any quotes or stage directions
        if buyer_text.startswith('"') and buyer_text.endswith('"'):
            buyer_text = buyer_text[1:-1]

        self.messages.append(AIMessage(content=buyer_text))

        # Check leverage impact of the turn
        leverage_shift = 0.5 if "?" in user_transcript else -0.5
        self.state_machine.on_buyer_speech(buyer_text, duration_sec=3.0, leverage_delta=leverage_shift, note="Standard turn exchange")

        return {
            "text": buyer_text,
            "is_interruption": False,
            "latency_ms": latency_ms,
            "patience": round(self.state_machine.patience, 1),
            "skepticism": round(self.state_machine.skepticism, 1),
            "deal_leverage": round(self.state_machine.deal_leverage, 1),
            "buzzwords": sm_result["buzzwords_found"],
        }
