"""
Triage engine: symptom extraction, severity classification, and safety guardrails.

This is the core logic for pediatric urgency routing.
"""

import re
from typing import Optional
from langdetect import detect, LangDetectException

from src.schema import (
    TriageRequest,
    TriageOutput,
    Severity,
    Language,
    EvidenceItem,
    validate_output,
)
from src.retrieval import get_retriever


# ============================================================================
# Red Flag Definitions (Hard Safety Rules)
# ============================================================================

EMERGENCY_RED_FLAGS = {
    "breathing_difficulty": [
        "can't breathe", "cannot breathe", "trouble breathing", "struggling to breathe",
        "gasping", "rapid breathing", "fast breathing", "wheezing", "stridor",
        "retractions", "unable to catch breath", "difficulty breathing",
        "تنفس صعب", "صعوبة في التنفس", "لا يستطيع التنفس", "اختناق",
    ],
    "blue_lips": [
        "blue lips", "blue tongue", "blue nails", "cyanosis", "cyanotic",
        "lipsareblue", "lips turn blue", "tongue is blue",
        "لسان أزرق", "شفاه زرقاء", "أظافر زرقاء", "زرقاء",
    ],
    "seizure": [
        "seizure", "seizures", "convulsion", "convulsions", "fitting",
        "jerking", "twitching", "unconscious", "unresponsive", "cannot wake",
        "hard to wake", "lethargy", "lethargic", "collapsed", "passed out",
        "نوبة", "تشنج", "فقدان الوعي", "لا يستيقظ", "بدون وعي",
    ],
    "severe_pain": [
        "severe pain", "worst pain", "unbearable pain", "screaming",
        "ألم شديد", "ألم لا يطاق", "الصراخ من الألم",
    ],
    "bleeding": [
        "bleeding", "heavy bleeding", "cannot stop bleeding", "blood loss",
        "coughing blood", "vomiting blood", "bloody vomit",
        "نزيف", "نزيف حاد", "نزيف دموي",
    ],
    "stiff_neck": [
        "stiff neck", "neck stiffness", "cannot bend neck",
        "رقبة صلبة", "تصلب الرقبة", "لا يمكن ثني الرقبة",
    ],
}

HIGH_SEVERITY_FLAGS = {
    "fever_infant": [
        "fever baby under 3 months", "fever newborn", "baby under 3 months temperature",
        "3 months old fever", "infant fever", "baby fever under 12 weeks",
        "حمى الرضيع", "طفل رضيع حمى", "حديث الولادة حمى",
    ],
    "high_fever": [
        "104", "40.5", "41", "fever 105", "very high fever", "extremely high fever",
        "104 f", "40 c", "persistent high fever", "high fever", "105 f",
    ],
    "purple_rash": [
        "purple rash", "petechial rash", "non-blanching rash", "dark red rash",
        "non blanching", "doesn't fade", "doesn't blanch",
        "طفح أرجواني", "طفح أحمر داكن",
    ],
    "dehydration_severe": [
        "no tears", "dry mouth", "no urine", "sunken eyes", "very lethargic",
        "extreme dehydration", "severe dehydration", "no wet diaper",
        "بدون دموع", "فم جاف", "لا بول", "عيون غارقة", "جفاف شديد",
    ],
}

MONITOR_FLAGS = {
    "fever_duration": ["fever for days", "fever for week", "persistent fever"],
    "vomiting": ["vomiting", "cannot keep anything down", "repeated vomiting"],
    "diarrhea": ["diarrhea", "loose stools"],
    "rash": ["rash", "spots"],
}


# ============================================================================
# Symptom Extraction
# ============================================================================

def extract_language(text: str) -> Language:
    """Detect language of input (English or Arabic)."""
    try:
        detected = detect(text)
        if detected == "ar":
            return Language.AR
        else:
            return Language.EN
    except LangDetectException:
        # Default to English if detection fails
        return Language.EN


def extract_symptoms(text: str) -> list[str]:
    """Extract symptom keywords from text."""
    symptoms = set()
    text_lower = text.lower()

    # Add keywords explicitly mentioned (but skip negated ones)
    keywords = [
        "cough", "fever", "vomiting", "diarrhea", "rash", "breathing", "pain",
        "cold", "flu", "cough", "sneeze", "runny nose", "sore throat",
        "ear pain", "abdominal pain", "belly", "stomach", "head", "headache",
        "lethargy", "drowsy", "irritable",
        # Injury/wound symptoms
        "cuts", "cut", "wound", "injury", "injure", "scrape", "scratch", "bruise",
        "symptoms",
        "السعال", "حمى", "قيء", "إسهال", "طفح", "تنفس", "ألم",
    ]

    for keyword in keywords:
        if keyword.lower() in text_lower:
            # Find position of keyword
            idx = text_lower.find(keyword.lower())
            if idx >= 0:
                # Get context before keyword (last 20 chars)
                start = max(0, idx - 20)
                before_text = text_lower[start:idx].strip()
                
                # Check if negated: ends with no, not, without, n't
                is_negated = (
                    before_text.endswith("no") or 
                    before_text.endswith("not") or 
                    before_text.endswith("without") or 
                    before_text.endswith("n't")
                )
                
                if not is_negated:
                    symptoms.add(keyword)

    return list(symptoms)[:10]  # Top 10


def detect_red_flags(text: str) -> list[str]:
    """Detect emergency and high-severity red flags."""
    detected = []
    text_lower = text.lower()

    # Normalize common phrase variations
    text_lower = text_lower.replace("can't", "cannot").replace("doesn't", "does not")
    text_lower = text_lower.replace("can't breathe", "cannot breathe")
    text_lower = text_lower.replace("lips turn", "lips are turning").replace("lips are blue", "blue lips")
    text_lower = text_lower.replace("turning blue", "blue")  # "lips turning blue" → "lips blue"
    
    def _keyword_not_negated(keyword: str, text: str) -> bool:
        """Check if keyword appears and is not negated by common negation words."""
        if keyword not in text:
            return False
        # If keyword preceded immediately by negation, it's negated
        negations = ["no ", "not ", "without ", "n't "]
        for neg in negations:
            if (neg + keyword) in text:
                return False
        return True
    
    for category, keywords in EMERGENCY_RED_FLAGS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if _keyword_not_negated(keyword_lower, text_lower):
                detected.append(category)
                break
            # Also check for related patterns (e.g., "blue" alone for cyanosis)
            if category == "blue_lips":
                if _keyword_not_negated("blue", text_lower) and ("lip" in text_lower or "tongue" in text_lower or "nail" in text_lower):
                    detected.append(category)
                    break

    for category, keywords in HIGH_SEVERITY_FLAGS.items():
        for keyword in keywords:
            if _keyword_not_negated(keyword.lower(), text_lower):
                detected.append(category)
                break
    
    # Also detect MONITOR-level flags that affect classification
    for category, keywords in MONITOR_FLAGS.items():
        for keyword in keywords:
            if _keyword_not_negated(keyword.lower(), text_lower):
                detected.append(category)
                break

    return list(set(detected))


def extract_temperature(text: str) -> tuple[Optional[float], Optional[str]]:
    """Extract temperature value and unit."""
    # Look for patterns like "39 C", "102 F", "40°C", etc.
    patterns = [
        r"(\d+\.?\d*)\s*[°]?[CF]",  # 39°C or 102 F
        r"(\d+\.?\d*)\s*degrees?\s*[CF]",  # 39 degrees C
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                temp = float(matches[0])
                # Determine unit based on value
                if temp > 50:  # Likely Fahrenheit
                    unit = "F"
                else:
                    unit = "C"
                return temp, unit
            except ValueError:
                pass

    return None, None


def extract_age(text: str) -> Optional[int]:
    """Extract child's age in months."""
    patterns = [
        r"(\d+)\s*(?:month|months|mo)",  # 6 months, 6 mo
        r"(\d+)\s*(?:year|years|y|yo)",  # Convert years to months
        r"(\d+\.\d+)\s*(?:week|weeks)",  # Convert weeks to months
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                value = float(matches[0])
                # Convert to months
                if "year" in pattern or "y" in pattern:
                    return int(value * 12)
                elif "week" in pattern:
                    return int(value * 4.3)
                else:
                    return int(value)
            except ValueError:
                pass

    return None


# ============================================================================
# Severity Classification
# ============================================================================

def classify_severity(
    red_flags: list[str],
    symptoms: list[str],
    age_months: Optional[int],
    temperature: Optional[float],
    temperature_unit: Optional[str],
    retriever,
) -> tuple[Severity, float, list[str], bool]:
    """
    Classify symptom urgency based on medical evidence.

    Returns:
        (severity, confidence, reasoning_notes, is_weak_retrieval)
    """
    reasoning = []

    # Hard rules: Emergency red flags always trump everything
    emergency_categories = [
        "breathing_difficulty", "blue_lips", "seizure",
        "severe_pain", "bleeding", "stiff_neck"
    ]
    if any(cat in red_flags for cat in emergency_categories):
        reasoning.append("[EMERGENCY] Red flag detected")
        return Severity.EMERGENCY, 0.95, reasoning, False

    # Check for very high fever
    if temperature is not None:
        temp_f = temperature
        if temperature_unit == "C":
            temp_f = (temperature * 9/5) + 32
        
        if temp_f > 104:
            reasoning.append(f"[WARNING] Very high fever ({temperature}{temperature_unit})")
            if "high_fever" not in red_flags:
                red_flags.append("high_fever")

    # High-severity conditions (non-emergency)
    high_severity = []
    
    # Infant fever under 12 months with any fever
    if age_months is not None and age_months < 12 and temperature is not None:
        temp_f = temperature
        if temperature_unit == "C":
            temp_f = (temperature * 9/5) + 32
        if temp_f >= 100.4 or temperature >= 38:
            high_severity.append("fever_infant")
            reasoning.append(f"[WARNING] Fever in infant under 12 months (age: {age_months}mo)")
    
    # Other high-severity red flags
    for flag in ["high_fever", "purple_rash", "stiff_neck", "dehydration_severe"]:
        if flag in red_flags:
            high_severity.append(flag)
            reasoning.append(f"[WARNING] {flag} detected")

    if high_severity:
        reasoning.append(f"ESCALATE to see-doctor: {', '.join(high_severity)}")
        return Severity.SEE_DOCTOR, 0.85, reasoning, False

    # Retrieve evidence with weak-detection
    evidence = []
    is_weak_retrieval = False
    
    if symptoms:
        # Use severity preference if high-severity flag present
        severity_filter = None
        if high_severity:
            severity_filter = "HIGH"
        
        evidence, is_weak_retrieval = retriever.search_by_keywords(
            symptoms, 
            k=6,
            age_months=age_months,
            minimum_relevance_threshold=0.3
        )
        
        if evidence:
            severities = [e.get("severity_relevance", "unknown") for e in evidence]
            reasoning.append(f"Retrieved evidence severity: {set(severities)}")
            if is_weak_retrieval:
                reasoning.append("[WEAK RETRIEVAL] < 2 relevant chunks found")
    
    # Classify based on pattern: symptoms, severity evidence, temperature, and red flags
    has_symptoms = len(symptoms) > 0
    has_minor_flags = len(red_flags) > 0
    
    # No symptoms = need more info
    if not has_symptoms and not has_minor_flags and temperature is None:
        reasoning.append("Insufficient information to assess")
        return Severity.NEED_MORE_INFO, 0.4, reasoning, is_weak_retrieval
    
    # Weak retrieval on medical query → uncertainty
    if has_symptoms and is_weak_retrieval and not evidence:
        reasoning.append("Insufficient retrieved evidence for medical query")
        return Severity.NEED_MORE_INFO, 0.4, reasoning, is_weak_retrieval
    
    # Specific conditions: vomiting/diarrhea symptoms → monitor (unless severe dehydration → see doctor)
    vomiting_like_symptoms = any(sym in [s.lower() for s in symptoms] for sym in ["vomit", "vomiting", "diarrhea", "diarrh"])
    has_vomiting_flag = "vomiting" in red_flags or "diarrhea" in red_flags
    if vomiting_like_symptoms or has_vomiting_flag:
        if "dehydration_severe" in red_flags:
            return Severity.SEE_DOCTOR, 0.80, reasoning, is_weak_retrieval
        reasoning.append("Monitor for dehydration/ongoing illness")
        return Severity.MONITOR, 0.70, reasoning, is_weak_retrieval
    
    # If symptoms present but no red flags
    if has_symptoms and not has_minor_flags:
        # Low fever + normal behavior = likely mild
        # Check if temperature is normal or low
        is_normal_temp = True
        if temperature is not None:
            temp_f = temperature
            if temperature_unit == "C":
                temp_f = (temperature * 9/5) + 32
            is_normal_temp = temp_f < 101  # Under 101°F is not high fever
        
        if is_normal_temp:
            reasoning.append("Symptoms with normal temperature, no red flags")
            return Severity.MILD, 0.75, reasoning, is_weak_retrieval
        else:
            reasoning.append("Symptoms with elevated temperature, monitoring needed")
            return Severity.MONITOR, 0.60, reasoning, is_weak_retrieval
    
    # Any other combination of symptoms with potential flags
    if has_symptoms:
        reasoning.append("Symptoms present, monitoring recommended")
        return Severity.MONITOR, 0.60, reasoning, is_weak_retrieval
    
    # Fallback: unclear input
    reasoning.append("Insufficient information to assess")
    return Severity.NEED_MORE_INFO, 0.4, reasoning, is_weak_retrieval


# ============================================================================
# Triage Engine
# ============================================================================

def run_triage(request: TriageRequest) -> TriageOutput:
    """
    Run complete pediatric triage on symptom input.

    Args:
        request: Parent symptom description and metadata

    Returns:
        Structured triage output with severity, evidence, and guidance
    """
    retriever = get_retriever()

    # Detect language
    detected_lang = extract_language(request.symptom_description)
    language = request.language or detected_lang

    # Extract structured info from symptom description
    symptoms = extract_symptoms(request.symptom_description)
    red_flags = detect_red_flags(request.symptom_description)
    temp_val, temp_unit = extract_temperature(request.symptom_description)
    age_months = request.child_age_months or extract_age(request.symptom_description)

    # Override with explicit values
    if request.temperature is not None:
        temp_val = request.temperature
    if request.temperature_unit is not None:
        temp_unit = request.temperature_unit.value

    # Add reported red flags
    red_flags.extend(request.red_flags_reported)

    # Classify severity
    severity, confidence, reasoning_notes, is_weak_retrieval = classify_severity(
        red_flags=red_flags,
        symptoms=symptoms,
        age_months=age_months,
        temperature=temp_val,
        temperature_unit=temp_unit,
        retriever=retriever,
    )

    # Retrieve evidence for UI display
    query = request.symptom_description
    evidence_chunks, _ = retriever.search(
        query, 
        k=6,
        age_months=age_months,
        minimum_relevance_threshold=0.3,
        max_context_chunks=4
    )

    retrieved_evidence = []
    for chunk in evidence_chunks:
        # Create excerpt (first 300 chars)
        excerpt = chunk["text"][:300]
        if len(chunk["text"]) > 300:
            excerpt += "..."

        retrieved_evidence.append(
            EvidenceItem(
                chunk_id=chunk["chunk_id"],
                source_name=chunk["source_name"],
                source_file=chunk["source_file"],
                source_url=chunk["source_url"],
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                section_title=chunk.get("section_title", ""),
                severity_relevance=chunk.get("severity_relevance", ""),
                excerpt=excerpt,
                relevance_reason=f"Matched symptoms. Topic: {chunk.get('topic', 'general')}",
            )
        )

    # Generate parent-facing response
    if language == Language.AR:
        summary, action, diagnosis_refusal, escalation = _generate_ar_response(
            severity, confidence, symptoms, red_flags, evidence_chunks, is_weak_retrieval
        )
    else:
        summary, action, diagnosis_refusal, escalation = _generate_en_response(
            severity, confidence, symptoms, red_flags, evidence_chunks, is_weak_retrieval
        )

    # Determine follow-up question if needed
    follow_up = None
    if severity == Severity.NEED_MORE_INFO:
        follow_up = _get_follow_up_question(language, symptoms)

    # Build output
    output = TriageOutput(
        language=language,
        patient_age_months=age_months,
        temperature_value=temp_val,
        temperature_unit=temp_unit,
        extracted_symptoms=symptoms,
        red_flags=red_flags,
        retrieved_evidence=retrieved_evidence,
        severity=severity,
        confidence=round(confidence, 2),
        uncertainty_flag=(severity == Severity.NEED_MORE_INFO),
        summary=summary,
        reasoning="; ".join(reasoning_notes),
        recommended_action=action,
        diagnosis_refusal=diagnosis_refusal,
        escalation_required=(severity in [Severity.EMERGENCY, Severity.SEE_DOCTOR]),
        follow_up_question=follow_up,
    )

    # Validate output
    is_valid, errors = validate_output(output)
    if not is_valid:
        # Log validation errors but don't fail - apply safety defaults
        for error in errors:
            print(f"⚠️ Validation warning: {error}")

        # Apply safety overrides
        if severity == Severity.EMERGENCY:
            output.escalation_required = True
            output.diagnosis_refusal = True

    return output


def _generate_en_response(
    severity: Severity,
    confidence: float,
    symptoms: list[str],
    red_flags: list[str],
    evidence_chunks: list[dict],
    is_weak_retrieval: bool,
) -> tuple[str, str, bool, bool]:
    """Generate English parent-facing response."""
    summary = ""
    action = ""
    diagnosis_refusal = False
    escalation = False

    if severity == Severity.EMERGENCY:
        summary = (
            "Based on the symptoms you described, this may be a medical emergency. "
            "Your child may need immediate medical attention."
        )
        action = "Call 911 or go to the nearest emergency room immediately."
        diagnosis_refusal = True
        escalation = True

    elif severity == Severity.SEE_DOCTOR:
        summary = (
            "The symptoms you described suggest your child should be evaluated by a "
            "healthcare provider soon. This is not a diagnosis, but professional "
            "evaluation is recommended."
        )
        action = (
            "Contact your pediatrician or urgent care clinic. If you cannot reach them, "
            "visit an urgent care center or emergency room."
        )
        diagnosis_refusal = True
        escalation = True

    elif severity == Severity.MONITOR:
        summary = (
            "Based on the information provided, the symptoms may be manageable at home "
            "with close monitoring. However, watch carefully for any worsening."
        )
        action = (
            "Monitor your child closely. Keep them hydrated and comfortable. "
            "Contact a doctor if symptoms worsen, persist, or new symptoms appear."
        )
        diagnosis_refusal = False

    elif severity == Severity.MILD:
        summary = (
            "The symptoms you described do not appear to be concerning at this time. "
            "Continue routine care and monitoring."
        )
        action = (
            "Monitor at home. Provide comfort care. Contact a doctor if symptoms change "
            "or you have concerns."
        )
        diagnosis_refusal = False

    else:  # NEED_MORE_INFO
        summary = (
            "I don't have enough information to assess your child's condition accurately. "
            "Please provide more details so I can help."
        )
        action = (
            "Answer the follow-up question below, or contact your pediatrician "
            "if you're worried."
        )
        # Refuse diagnosis only if there IS medical evidence AND retrieval was NOT weak
        # Weak retrieval = out-of-scope (not a medical query) → don't refuse
        # Strong retrieval with vague symptoms = medical but unclear → refuse
        diagnosis_refusal = len(evidence_chunks) > 0 and not is_weak_retrieval

    return summary, action, diagnosis_refusal, escalation


def _generate_ar_response(
    severity: Severity,
    confidence: float,
    symptoms: list[str],
    red_flags: list[str],
    evidence_chunks: list[dict],
    is_weak_retrieval: bool,
) -> tuple[str, str, bool, bool]:
    """Generate Arabic parent-facing response."""
    summary = ""
    action = ""
    diagnosis_refusal = False
    escalation = False

    if severity == Severity.EMERGENCY:
        summary = (
            "بناءً على الأعراض التي وصفتيها، قد تكون هذه حالة طبية طارئة. "
            "قد يحتاج طفلك إلى عناية طبية فورية."
        )
        action = "اتصلي برقم الطوارئ أو توجهي إلى أقرب مستشفى فوراً."
        diagnosis_refusal = True
        escalation = True

    elif severity == Severity.SEE_DOCTOR:
        summary = (
            "الأعراض التي وصفتيها تشير إلى أن طفلك يحتاج إلى تقييم من قبل متخصص "
            "في الرعاية الصحية قريباً. هذا ليس تشخيصاً، لكن الفحص المهني موصى به."
        )
        action = (
            "اتصلي بطبيب الأطفال أو عيادة الرعاية الحثيثة. إذا لم تتمكني من الوصول إليهم، "
            "توجهي إلى عيادة رعاية حثيثة أو مستشفى."
        )
        diagnosis_refusal = True
        escalation = True

    elif severity == Severity.MONITOR:
        summary = (
            "بناءً على المعلومات المقدمة، قد تكون الأعراض قابلة للمراقبة في المنزل "
            "مع الانتباه الشديد لأي تطورات."
        )
        action = (
            "راقبي طفلك بعناية. تأكدي من شرب السوائل والراحة الكافية. "
            "اتصلي بالطبيب إذا تفاقمت الأعراض أو استمرت."
        )
        diagnosis_refusal = False

    elif severity == Severity.MILD:
        summary = (
            "الأعراض التي وصفتيها لا تبدو مقلقة حالياً. استمري في الرعاية العادية."
        )
        action = (
            "راقبي طفلك في المنزل. قدمي له الراحة والراحة. اتصلي بالطبيب إذا تغيرت الأعراض."
        )
        diagnosis_refusal = False

    else:  # NEED_MORE_INFO
        summary = (
            "ليس لديّ معلومات كافية لتقييم حالة طفلك بدقة. يرجى توفير المزيد من التفاصيل."
        )
        action = (
            "أجيبي على السؤال التالي، أو اتصلي بطبيب الأطفال إذا كنت قلقة."
        )
        # Refuse diagnosis only if there IS medical evidence AND retrieval was NOT weak
        diagnosis_refusal = len(evidence_chunks) > 0 and not is_weak_retrieval

    return summary, action, diagnosis_refusal, escalation


def _get_follow_up_question(language: Language, symptoms: list[str]) -> str:
    """Generate follow-up question for vague inputs."""
    if language == Language.AR:
        if "fever" in " ".join(symptoms).lower() or "حمى" in " ".join(symptoms):
            return "ما درجة حرارة طفلك؟ وكم من الوقت يعاني من الحمى؟"
        elif "رash" in " ".join(symptoms).lower() or "طفح" in " ".join(symptoms):
            return "أين تظهر الطفح؟ هل تختفي عند الضغط عليها؟"
        else:
            return "هل يستطيع طفلك الشرب والأكل بشكل طبيعي؟"
    else:
        if "fever" in " ".join(symptoms).lower():
            return "What is your child's temperature? How long have they had a fever?"
        elif "rash" in " ".join(symptoms).lower():
            return "Where is the rash? Does it fade when you press on it?"
        else:
            return "Can your child drink and eat normally?"
