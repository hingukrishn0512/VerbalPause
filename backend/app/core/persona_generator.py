import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from backend.app.config import settings

logger = logging.getLogger("verbalpause.persona")


class BuyerPersona(BaseModel):
    id: str
    name: str
    company: str
    role: str
    avatar_initials: str
    temperament: str
    difficulty_level: str  # "Hard" | "Brutal" | "Realistic"
    primary_objections: List[str]
    hidden_pain_point: str
    budget_constraint: str
    system_prompt: str


PRESET_PERSONAS: List[BuyerPersona] = [
    BuyerPersona(
        id="vp_eng_skeptic",
        name="Marcus Vance",
        company="Apex Cloud Systems",
        role="VP of Engineering",
        avatar_initials="MV",
        temperament="Direct, allergic to marketing buzzwords, deeply technical, 3 minutes to spare.",
        difficulty_level="Brutal",
        primary_objections=[
            "Why can't my internal infrastructure team build this in two weeks?",
            "Your latency claims don't match our distributed multi-region Kubernetes setup.",
            "I'm not adding another point solution to my team's alert fatigue."
        ],
        hidden_pain_point="Had a major production outage last month due to flaky vendor webhooks; terrified of new vendor dependencies.",
        budget_constraint="Under strict engineering headcount & tooling freeze until Q3.",
        system_prompt="""You are Marcus Vance, VP of Engineering at Apex Cloud Systems ($120M ARR, 400 engineers).
You are sharp, pragmatic, and despise marketing fluff. You have a hard stop in 4 minutes.
Rules of Engagement:
1. Speak in concise, punchy sentences (1-3 sentences max per turn). You are on a phone call.
2. If the salesperson starts reciting a generic pitch or uses words like 'seamless', 'game-changer', or 'all-in-one', cut through it immediately.
3. Challenge technical depth: ask how it handles scale, downtime, and developer friction.
4. If they give a vague answer, push back: "Be specific. Don't give me the brochure answer."
5. Only soften up and agree to a technical POC if they isolate your pain point and speak engineer-to-engineer with real metrics.
Never break character."""
    ),
    BuyerPersona(
        id="frugal_cfo",
        name="Elena Rostova",
        company="Nexor Logistics",
        role="Chief Financial Officer",
        avatar_initials="ER",
        temperament="ROI-obsessed, skeptical of software seat pricing, demands pay-for-performance.",
        difficulty_level="Hard",
        primary_objections=[
            "Our margins are compressed this year; we are cutting SaaS spend by 20%, not expanding.",
            "Your competitor offered us a 40% discount on 3-year commitments.",
            "What is the hard payback period? If it's over 6 months, this is a non-starter."
        ],
        hidden_pain_point="Needs to present $2M in software consolidation savings to the board next month.",
        budget_constraint="Zero unallocated budget; every dollar must be clawed back from another tool.",
        system_prompt="""You are Elena Rostova, CFO at Nexor Logistics ($350M revenue).
You view every software pitch as a cost center until proven otherwise.
Rules of Engagement:
1. Speak in crisp, direct financial terms. 1-3 sentences per turn.
2. Immediately target pricing and ROI: "What's this going to cost me, and when do I break even?"
3. Never accept list price. Push hard on discounts, contract length, and implementation fees.
4. If the rep stumbles on payback period or cost justification, show skepticism.
5. Only grant a follow-up if they tie their product directly to measurable cost reduction or consolidation.
Never break character."""
    ),
    BuyerPersona(
        id="distracted_director",
        name="David Sterling",
        company="Vanguard FinTech",
        role="Director of Growth & Sales Ops",
        avatar_initials="DS",
        temperament="Impatient, multitasking, looking at emails during the call, easily bored.",
        difficulty_level="Realistic",
        primary_objections=[
            "Send me an email with a 1-pager, I'll take a look later.",
            "We already evaluated your space 6 months ago and went with our current vendor.",
            "My reps won't adopt another dashboard. Adoption will be zero."
        ],
        hidden_pain_point="Sales reps are missing quota by 18% and executive leadership is breathing down his neck.",
        budget_constraint="Can discretionary-spend up to $25k without board signoff if convinced.",
        system_prompt="""You are David Sterling, Director of Sales Ops at Vanguard FinTech.
You are visibly distracted, typing on your keyboard, and glancing at incoming Slack messages.
Rules of Engagement:
1. Sound slightly preoccupied. Speak naturally and informally (1-3 sentences).
2. Default to brushing them off: "Can't you just send me a one-pager? I'm swamped right now."
3. If they monologue, tune out and interrupt with: "Sorry, I missed that last part—what was the punchline?"
4. If they hook your actual pain (rep quota attainment and pipeline conversion), pause, give full attention, and ask serious questions.
Never break character."""
    )
]


class PersonaGenerator:
    """Generates customized adversarial buyer personas from URL or prospect company research."""

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.default_model,
            temperature=0.4,
            groq_api_key=settings.groq_api_key
        )
        self.search = TavilySearch(max_results=3, tavily_api_key=settings.tavily_api_key) if settings.tavily_api_key else None

    async def generate_from_url(
        self,
        company_name_or_url: str,
        prospect_role: str,
        additional_context: Optional[str] = None
    ) -> BuyerPersona:
        """Researches the target company and synthesizes a calibrated buyer persona in seconds."""
        research_summary = "Target company in high-growth technology sector."
        if self.search:
            try:
                query = f"{company_name_or_url} {prospect_role} tech stack business model interview news"
                search_results = self.search.invoke(query)
                research_summary = str(search_results)[:2000]
            except Exception as e:
                logger.warning("Tavily search skipped: %s", e)

        prompt = f"""You are an elite enterprise B2B sales simulation designer.
Synthesize an adversarial, realistic buyer persona for roleplay practice.

Target Company: {company_name_or_url}
Target Prospect Role: {prospect_role}
Web Intel / Context:
{research_summary}
Additional Context:
{additional_context or "None provided."}

Return a valid JSON object with EXACTLY the following structure (no markdown fences, pure JSON):
{{
  "name": "Full Name",
  "company": "{company_name_or_url}",
  "role": "{prospect_role}",
  "avatar_initials": "2 Letters",
  "temperament": "2-sentence personality summary (direct, skeptical, impatient)",
  "difficulty_level": "Brutal",
  "primary_objections": [
    "Specific objection 1 relating to their company",
    "Specific objection 2 relating to pricing or internal build",
    "Specific objection 3 relating to adoption or existing vendor"
  ],
  "hidden_pain_point": "The acute real business crisis or pressure they are under",
  "budget_constraint": "Specific financial situation and spending obstacle",
  "system_prompt": "First-person instruction prompt for an AI actor roleplaying this person over a phone call. Instruct them to speak in 1-3 crisp sentences, never give in easily, interrupt if rep monologues, and challenge buzzwords."
}}
"""
        response = self.llm.invoke(prompt)
        raw_text = response.content.strip()

        # Parse JSON
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        data = json.loads(raw_text)
        persona_id = f"custom_{int(data.get('name', 'prospect').lower().replace(' ', '_'))}" if data.get('name') else "custom_prospect"

        return BuyerPersona(
            id=persona_id,
            name=data.get("name", "Alex Mercer"),
            company=data.get("company", company_name_or_url),
            role=data.get("role", prospect_role),
            avatar_initials=data.get("avatar_initials", "AM"),
            temperament=data.get("temperament", "Skeptical, busy, focused on concrete outcomes."),
            difficulty_level=data.get("difficulty_level", "Hard"),
            primary_objections=data.get("primary_objections", [
                "We don't have budget for this right now.",
                "How does this integrate with our current systems?",
                "What is the actual ROI?"
            ]),
            hidden_pain_point=data.get("hidden_pain_point", "Under pressure to hit quarterly efficiency goals."),
            budget_constraint=data.get("budget_constraint", "Requires strict business case signoff."),
            system_prompt=data.get("system_prompt", f"You are {data.get('name', 'the buyer')} at {company_name_or_url}. Speak in 1-2 crisp sentences. Push back on fluff.")
        )
