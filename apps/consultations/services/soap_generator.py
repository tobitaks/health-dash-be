"""
AI-powered SOAP Notes Generator using LiteLLM.
"""

import json
import logging

import litellm
from django.conf import settings

logger = logging.getLogger(__name__)

# System prompt for the medical documentation assistant
SOAP_SYSTEM_PROMPT = """You are a medical documentation assistant helping physicians create SOAP notes
for a clinic management system. Your role is to generate professional, accurate SOAP notes
based on the provided patient information.

Guidelines:
1. SUBJECTIVE (S): Summarize the chief complaint in clinical language. Include
   relevant history of present illness details if available from patient history.

2. OBJECTIVE (O): Start with vital signs, then describe expected physical
   examination findings based on the chief complaint. Use appropriate medical
   terminology.

3. ASSESSMENT (A): Provide differential diagnoses based on the subjective and
   objective findings. Use hedging language like "likely", "consider", "rule out"
   since you are suggesting, not diagnosing.

4. PLAN (P): Suggest a reasonable treatment plan including:
   - Diagnostic workup if needed
   - Treatment recommendations (AVOID medications the patient is allergic to)
   - Follow-up timeline
   - Patient education points

Important:
- Be concise but comprehensive
- Use standard medical abbreviations appropriately
- This is a DRAFT for physician review - clearly indicate uncertainty
- Consider patient history for context but don't repeat old diagnoses as current
- ALWAYS check patient allergies before suggesting medications
- Consider existing medical conditions and current medications for drug interactions
- Format each section as a clear, readable paragraph or bullet list as appropriate

You MUST respond with a valid JSON object in exactly this format:
{
  "subjective": "...",
  "objective": "...",
  "assessment": "...",
  "plan": "..."
}

Do not include any text outside the JSON object."""


def build_soap_context(consultation, patient_history) -> dict:
    """
    Build context dictionary from consultation and patient history.

    Args:
        consultation: The current Consultation model instance
        patient_history: QuerySet of previous Consultation instances for the patient

    Returns:
        Dictionary with chief_complaint, vital_signs, patient_history, and patient_medical_info
    """
    patient = consultation.patient

    return {
        "chief_complaint": consultation.chief_complaint or "",
        "vital_signs": {
            "blood_pressure": (
                f"{consultation.bp_systolic}/{consultation.bp_diastolic} mmHg"
                if consultation.bp_systolic and consultation.bp_diastolic
                else None
            ),
            "temperature": (
                f"{consultation.temperature}°{consultation.temperature_unit}"
                if consultation.temperature
                else None
            ),
            "heart_rate": f"{consultation.heart_rate} bpm" if consultation.heart_rate else None,
            "respiratory_rate": (
                f"{consultation.respiratory_rate}/min" if consultation.respiratory_rate else None
            ),
            "oxygen_saturation": (
                f"{consultation.oxygen_saturation}%" if consultation.oxygen_saturation else None
            ),
            "weight": (
                f"{consultation.weight} {consultation.weight_unit}" if consultation.weight else None
            ),
            "height": (
                f"{consultation.height} {consultation.height_unit}" if consultation.height else None
            ),
        },
        "patient_medical_info": {
            "allergies": patient.allergies if patient.allergies else [],
            "medical_conditions": patient.medical_conditions if patient.medical_conditions else [],
            "current_medications": patient.current_medications or "",
            "blood_type": patient.blood_type or "",
        },
        "patient_history": [
            {
                "date": str(c.consultation_date),
                "chief_complaint": c.chief_complaint or "",
                "diagnosis": c.diagnosis or "",
                "assessment": c.soap_assessment or "",
            }
            for c in patient_history
        ],
    }


def _format_vitals(vital_signs: dict) -> str:
    """Format vital signs dictionary into readable text."""
    parts = []
    for key, value in vital_signs.items():
        if value:
            label = key.replace("_", " ").title()
            parts.append(f"- {label}: {value}")
    return "\n".join(parts) if parts else "No vital signs recorded."


def _format_history(patient_history: list) -> str:
    """Format patient history into readable text."""
    if not patient_history:
        return "No previous consultations on record."

    parts = []
    for visit in patient_history:
        entry = f"- {visit['date']}: {visit['chief_complaint']}"
        if visit.get("diagnosis"):
            entry += f" (Dx: {visit['diagnosis']})"
        parts.append(entry)
    return "\n".join(parts)


def _format_medical_info(medical_info: dict) -> str:
    """Format patient medical information into readable text."""
    parts = []

    allergies = medical_info.get("allergies", [])
    if allergies:
        parts.append(f"- Allergies: {', '.join(allergies)}")
    else:
        parts.append("- Allergies: None known")

    conditions = medical_info.get("medical_conditions", [])
    if conditions:
        parts.append(f"- Medical Conditions: {', '.join(conditions)}")
    else:
        parts.append("- Medical Conditions: None known")

    medications = medical_info.get("current_medications", "")
    if medications:
        parts.append(f"- Current Medications: {medications}")
    else:
        parts.append("- Current Medications: None")

    blood_type = medical_info.get("blood_type", "")
    if blood_type:
        parts.append(f"- Blood Type: {blood_type}")

    return "\n".join(parts)


def _get_llm_kwargs():
    """Get LLM configuration from settings."""
    # Use DEFAULT_LLM_MODEL if set, otherwise auto-detect based on available API keys
    model_name = getattr(settings, "DEFAULT_LLM_MODEL", "") or ""

    if not model_name:
        # Auto-detect based on available API keys
        anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "") or ""
        openai_key = getattr(settings, "OPENAI_API_KEY", "") or ""

        if anthropic_key:
            model_name = "claude-sonnet-4-5-20250929"
        elif openai_key:
            model_name = "gpt-4o"
        else:
            raise ValueError("No LLM configured. Set DEFAULT_LLM_MODEL or an API key.")

    model_config = getattr(settings, "LLM_MODELS", {}).get(model_name, {})
    return {"model": model_name, **model_config}


async def generate_soap_with_ai(context: dict) -> dict:
    """
    Generate SOAP notes using LLM.

    Args:
        context: Dictionary containing chief_complaint, vital_signs, and patient_history

    Returns:
        Dictionary with subjective, objective, assessment, and plan fields
    """
    user_prompt = f"""Generate SOAP notes for this consultation:

CHIEF COMPLAINT:
{context['chief_complaint']}

VITAL SIGNS:
{_format_vitals(context['vital_signs'])}

PATIENT MEDICAL INFORMATION:
{_format_medical_info(context.get('patient_medical_info', {}))}

PATIENT HISTORY (recent consultations):
{_format_history(context['patient_history'])}

Generate appropriate SOAP notes based on this information. Remember this is a draft
for physician review - be helpful but indicate uncertainty appropriately.
IMPORTANT: Check allergies before suggesting any medications.

Respond with a JSON object containing: subjective, objective, assessment, plan"""

    messages = [
        {"role": "system", "content": SOAP_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = litellm.completion(messages=messages, **_get_llm_kwargs())
        content = response.choices[0].message.content.strip()

        # Try to parse JSON from the response
        # Handle case where response might have markdown code blocks
        if content.startswith("```"):
            # Extract JSON from markdown code block
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json"):
                    in_json = True
                    continue
                elif line.startswith("```"):
                    in_json = False
                    continue
                elif in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        soap_data = json.loads(content)

        return {
            "subjective": soap_data.get("subjective", ""),
            "objective": soap_data.get("objective", ""),
            "assessment": soap_data.get("assessment", ""),
            "plan": soap_data.get("plan", ""),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse SOAP response as JSON: {e}")
        logger.error(f"Response content: {content}")
        raise ValueError("AI response was not valid JSON. Please try again.")
    except Exception as e:
        logger.exception("Error generating SOAP notes")
        raise
