import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# High-risk buzzwords that trigger buyer skepticism and decay patience
COMMON_BUZZWORDS = {
    "cutting-edge", "game-changer", "synergy", "seamless", "all-in-one",
    "disruptive", "robust", "paradigm shift", "best-in-class", "silver bullet",
    "state-of-the-art", "frictionless", "turnkey", "holistic", "scalable solution",
    "market leader", "revolutionary", "hyper-growth"
}

INTERRUPTION_TEMPLATES = [
    "Sorry to cut in, but I have a hard stop in 3 minutes. What is the actual bottom-line ROI here?",
    "Hold on a second. That sounds like marketing fluff. How does this actually integrate with our existing stack?",
    "Wait, let me pause you right there. What does this actually cost? Don't give me a range, give me real numbers.",
    "Alex, look—I've heard this exact pitch from three other vendors this week. What specifically makes you different?",
    "Hang on. You've been talking for a while. Why should my engineering team care about this right now?",
]


class LeverageDataPoint(BaseModel):
    timestamp_sec: float
    leverage: float  # -10 to +10
    patience: float  # 0 to 100
    skepticism: float  # 0 to 100
    speaker: str  # "user" | "buyer"
    event_type: str = "normal"  # "normal" | "interruption" | "leverage_drop" | "leverage_gain"
    note: str = ""


class NegotiationStateMachine:
    """
    Real-time dynamic emotional state machine for adversarial AI buyers.
    Tracks buyer Patience, Skepticism, and Deal Leverage in full-duplex calls.
    """

    def __init__(
        self,
        initial_patience: float = 100.0,
        initial_skepticism: float = 50.0,
        initial_leverage: float = 0.0,
    ):
        self.patience = initial_patience
        self.skepticism = initial_skepticism
        self.deal_leverage = initial_leverage

        self.start_time = time.time()
        self.current_user_monologue_sec = 0.0
        self.total_user_talk_sec = 0.0
        self.total_buyer_talk_sec = 0.0

        self.user_turn_count = 0
        self.buyer_turn_count = 0
        self.buzzwords_used: List[str] = []
        self.questions_asked_by_user = 0
        self.interruptions_triggered = 0

        self.timeline: List[LeverageDataPoint] = [
            LeverageDataPoint(
                timestamp_sec=0.0,
                leverage=self.deal_leverage,
                patience=self.patience,
                skepticism=self.skepticism,
                speaker="system",
                note="Call started"
            )
        ]

    def elapsed_seconds(self) -> float:
        return round(time.time() - self.start_time, 1)

    def on_user_speech(self, text: str, duration_sec: float = 3.0) -> Dict[str, Any]:
        """
        Called when a candidate speaks. Updates monologue time, checks buzzwords,
        decays patience if monologuing, and determines if an active interruption should trigger.
        """
        self.user_turn_count += 1
        self.current_user_monologue_sec += duration_sec
        self.total_user_talk_sec += duration_sec
        text_lower = text.lower()

        # Check for discovery / question asking
        has_question = "?" in text or any(text_lower.startswith(w) for w in ["how", "what", "why", "where", "who", "could you", "tell me"])
        if has_question:
            self.questions_asked_by_user += 1
            # Asking good questions restores buyer patience and reduces skepticism
            self.patience = min(100.0, self.patience + 8.0)
            self.skepticism = max(10.0, self.skepticism - 5.0)
            self.deal_leverage = min(10.0, self.deal_leverage + 0.8)
            self.current_user_monologue_sec = 0.0  # reset monologue timer

        # Detect buzzwords
        found_buzzwords = [bw for bw in COMMON_BUZZWORDS if bw in text_lower]
        if found_buzzwords:
            self.buzzwords_used.extend(found_buzzwords)
            penalty = len(found_buzzwords) * 12.0
            self.patience = max(0.0, self.patience - penalty)
            self.skepticism = min(100.0, self.skepticism + penalty * 0.8)
            self.deal_leverage = max(-10.0, self.deal_leverage - 1.5)

        # Monologue penalty: if talking for > 12 seconds continuously
        if self.current_user_monologue_sec > 12.0:
            overage = self.current_user_monologue_sec - 12.0
            self.patience = max(0.0, self.patience - overage * 3.0)
            self.skepticism = min(100.0, self.skepticism + overage * 2.0)

        # Determine if an adversarial interruption should fire
        should_interrupt = False
        interrupt_reason = None
        interrupt_dialogue = None

        if self.current_user_monologue_sec >= 16.0 or self.patience <= 35.0:
            should_interrupt = True
            self.interruptions_triggered += 1
            template_idx = (self.interruptions_triggered - 1) % len(INTERRUPTION_TEMPLATES)
            interrupt_dialogue = INTERRUPTION_TEMPLATES[template_idx]
            interrupt_reason = f"Candidate monologued for {round(self.current_user_monologue_sec)}s without asking discovery questions."
            self.current_user_monologue_sec = 0.0  # reset after interrupt
            self.deal_leverage = max(-10.0, self.deal_leverage - 2.5)

        # Log timeline point
        t_sec = self.elapsed_seconds()
        event_tag = "interruption" if should_interrupt else ("leverage_drop" if found_buzzwords else "normal")
        note = interrupt_reason or (f"Buzzwords: {', '.join(found_buzzwords)}" if found_buzzwords else ("Good question" if has_question else ""))
        
        self.timeline.append(
            LeverageDataPoint(
                timestamp_sec=t_sec,
                leverage=round(self.deal_leverage, 1),
                patience=round(self.patience, 1),
                skepticism=round(self.skepticism, 1),
                speaker="user",
                event_type=event_tag,
                note=note
            )
        )

        return {
            "should_interrupt": should_interrupt,
            "interrupt_dialogue": interrupt_dialogue,
            "patience": round(self.patience, 1),
            "skepticism": round(self.skepticism, 1),
            "deal_leverage": round(self.deal_leverage, 1),
            "monologue_seconds": round(self.current_user_monologue_sec, 1),
            "buzzwords_found": found_buzzwords,
        }

    def on_buyer_speech(self, text: str, duration_sec: float = 3.0, leverage_delta: float = 0.0, note: str = ""):
        """Called when buyer speaks or finishes an answer."""
        self.buyer_turn_count += 1
        self.total_buyer_talk_sec += duration_sec
        self.current_user_monologue_sec = 0.0  # reset user monologue
        self.deal_leverage = max(-10.0, min(10.0, self.deal_leverage + leverage_delta))

        self.timeline.append(
            LeverageDataPoint(
                timestamp_sec=self.elapsed_seconds(),
                leverage=round(self.deal_leverage, 1),
                patience=round(self.patience, 1),
                skepticism=round(self.skepticism, 1),
                speaker="buyer",
                event_type="normal",
                note=note
            )
        )

    def get_summary(self) -> Dict[str, Any]:
        """Calculates post-call behavioral metrics and leverage breakdown."""
        total_time = self.total_user_talk_sec + self.total_buyer_talk_sec
        talk_ratio = round((self.total_user_talk_sec / total_time * 100), 1) if total_time > 0 else 50.0

        # Calculate final deal outcome based on leverage and skepticism
        if self.deal_leverage >= 4.0 and self.skepticism < 45.0:
            outcome = "Next Steps Secured (High Conviction)"
            score = 88 + min(12, int(self.deal_leverage))
        elif self.deal_leverage >= 0.0 and self.patience > 40.0:
            outcome = "Mild Interest (Needs Value Proof)"
            score = 68 + int(self.deal_leverage * 3)
        elif self.patience <= 30.0 or self.deal_leverage < -4.0:
            outcome = "Lost Deal (Buyer Impatience / Fluff Overload)"
            score = max(25, 50 + int(self.deal_leverage * 4))
        else:
            outcome = "Stalled in Committee (Pricing / Skepticism Friction)"
            score = 60 + int(self.deal_leverage * 2)

        return {
            "overall_score": score,
            "outcome": outcome,
            "final_leverage": round(self.deal_leverage, 1),
            "final_patience": round(self.patience, 1),
            "final_skepticism": round(self.skepticism, 1),
            "talk_to_listen_ratio": f"{talk_ratio}% User / {round(100 - talk_ratio, 1)}% Buyer",
            "ideal_talk_ratio": "45% User / 55% Buyer",
            "questions_asked": self.questions_asked_by_user,
            "buzzwords_used": list(set(self.buzzwords_used)),
            "interruptions_triggered": self.interruptions_triggered,
            "timeline": [dp.model_dump() for dp in self.timeline],
        }
