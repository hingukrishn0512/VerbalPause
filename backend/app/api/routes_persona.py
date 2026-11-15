from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.app.core.persona_generator import PersonaGenerator, BuyerPersona, PRESET_PERSONAS

router = APIRouter(prefix="/api/personas", tags=["Personas"])
generator = PersonaGenerator()


class GeneratePersonaRequest(BaseModel):
    company_name_or_url: str
    prospect_role: str
    additional_context: Optional[str] = None


@router.get("/presets", response_model=List[BuyerPersona])
def get_preset_personas():
    """Returns battle-tested adversarial buyer personas ready to roleplay immediately."""
    return PRESET_PERSONAS


@router.post("/generate", response_model=BuyerPersona)
async def generate_custom_persona(payload: GeneratePersonaRequest):
    """Researches target company and synthesizes a hyper-realistic adversarial buyer persona."""
    if not payload.company_name_or_url.strip() or not payload.prospect_role.strip():
        raise HTTPException(status_code=400, detail="Company and role are required.")

    try:
        persona = await generator.generate_from_url(
            company_name_or_url=payload.company_name_or_url.strip(),
            prospect_role=payload.prospect_role.strip(),
            additional_context=payload.additional_context
        )
        return persona
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate persona: {str(e)}")
