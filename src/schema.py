"""
Schema and validation for pediatric symptom triage output.

Defines the structured output contract and validation rules.
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, validator, field_validator


class Severity(str, Enum):
    """Allowed severity levels."""

    MILD = "mild"
    MONITOR = "monitor"
    SEE_DOCTOR = "see-doctor"
    EMERGENCY = "emergency"
    NEED_MORE_INFO = "need-more-info"


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    AR = "ar"


class TemperatureUnit(str, Enum):
    """Temperature units."""

    F = "F"
    C = "C"


class EvidenceItem(BaseModel):
    """Retrieved evidence chunk."""

    chunk_id: str
    source_name: str
    source_file: str
    source_url: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section_title: str
    severity_relevance: str
    excerpt: str = Field(
        ..., description="First 300 chars of chunk text for display"
    )
    relevance_reason: str = Field(
        ..., description="Why this evidence is relevant to the query"
    )


class TriageOutput(BaseModel):
    """Structured triage result."""

    language: Language = Field(..., description="Language of the response")
    patient_age_months: Optional[int] = Field(
        None, description="Child's age in months, null if not provided"
    )
    temperature_value: Optional[float] = Field(None, description="Temperature value")
    temperature_unit: Optional[TemperatureUnit] = Field(
        None, description="Temperature unit (F or C)"
    )
    duration: Optional[str] = Field(None, description="Symptom duration")
    extracted_symptoms: list[str] = Field(
        default_factory=list, description="Extracted symptoms from input"
    )
    red_flags: list[str] = Field(default_factory=list, description="Detected red flags")
    retrieved_evidence: list[EvidenceItem] = Field(
        default_factory=list, description="Retrieved supportive evidence"
    )
    severity: Severity = Field(..., description="Classified severity level")
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence score (0-1)"
    )
    uncertainty_flag: bool = Field(
        default=False, description="True if input is vague/incomplete"
    )
    summary: str = Field(..., description="Plain language summary for parent")
    reasoning: str = Field(..., description="Internal reasoning (for transparency)")
    recommended_action: str = Field(..., description="Next step for parent")
    diagnosis_refusal: bool = Field(
        default=False,
        description="True if system explicitly refuses diagnosis",
    )
    escalation_required: bool = Field(
        default=False,
        description="True if urgent medical attention needed",
    )
    follow_up_question: Optional[str] = Field(
        None, description="If severity is unclear, ask this question"
    )
    medical_disclaimer: str = Field(
        default="This assessment is not a medical diagnosis. Please consult a healthcare provider.",
        description="Standard medical disclaimer",
    )

    @validator("patient_age_months", pre=True)
    def validate_age(cls, v):
        if v is None:
            return None
        v = int(v)  # Convert float to int if needed
        if v < 0:
            raise ValueError("Age must be non-negative")
        return v

    @validator("temperature_value", pre=True)
    def validate_temperature(cls, v, values):
        if v is not None:
            # Be lenient - accept both F and C range
            if v < 35 or v > 107:  # 35 to 107 covers both C and F ranges
                raise ValueError(
                    "Temperature must be between 35 and 107 (handle both C and F)"
                )
        return v

    @validator("confidence")
    def validate_confidence(cls, v):
        if not (0 <= v <= 1):
            raise ValueError("Confidence must be between 0 and 1")
        return v


class TriageRequest(BaseModel):
    """Parent symptom input."""

    language: Optional[Language] = Field(None, description="Language preference (auto-detect if null)")
    child_age_months: Optional[int] = Field(None, description="Child's age in months")
    temperature: Optional[float] = Field(None, description="Temperature value")
    temperature_unit: Optional[TemperatureUnit] = Field(None, description="F or C")
    duration: Optional[str] = Field(None, description="How long symptoms lasted")
    symptom_description: str = Field(..., description="Free-text symptom description")
    red_flags_reported: list[str] = Field(
        default_factory=list,
        description="Red flags parent checked (breathing, blue lips, etc.)",
    )


def validate_output(output: TriageOutput) -> tuple[bool, list[str]]:
    """
    Validate triage output against schema and safety rules.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Severity-specific validation
    if output.severity == Severity.EMERGENCY:
        if not output.escalation_required:
            errors.append("Emergency severity MUST have escalation_required=True")
        if output.confidence < 0.7:
            errors.append("Emergency severity must have high confidence (>= 0.7)")

    elif output.severity == Severity.SEE_DOCTOR:
        if not output.diagnosis_refusal:
            errors.append(
                "See-doctor severity MUST have diagnosis_refusal=True (no diagnosis claim)"
            )

    elif output.severity == Severity.MONITOR:
        # Monitor doesn't require diagnosis refusal (it's not claiming diagnosis)
        pass

    # Evidence requirement for medical advice
    if output.severity != Severity.MILD:
        if len(output.retrieved_evidence) == 0:
            errors.append(
                f"{output.severity} severity must include retrieved evidence"
            )

    # Red flag consistency
    if len(output.red_flags) > 0:
        if output.severity == Severity.MILD:
            errors.append(
                "Mild severity cannot have red flags; should be monitor or higher"
            )

    # Out-of-scope handling
    if output.severity == Severity.NEED_MORE_INFO:
        if output.confidence > 0.5:
            errors.append(
                "Need-more-info should have low confidence (<= 0.5)"
            )
        if output.follow_up_question is None:
            errors.append(
                "Need-more-info must include a follow_up_question"
            )

    return (len(errors) == 0, errors)
