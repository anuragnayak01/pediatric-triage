"""
Streamlit UI for pediatric symptom triage.
"""

import streamlit as st
from datetime import datetime

from src.schema import Language, TriageRequest, Severity
from src.triage import run_triage


st.set_page_config(
    page_title="PediTriage · Pediatric Symptom Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* App background */
    .stApp { background-color: #f0f4f8; }

    .block-container {
        padding: 2rem 3rem 4rem !important;
        max-width: 1000px !important;
    }

    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: #0f2744 !important;
        font-style: normal !important;
    }

    /* Fix italic markdown headings */
    h3 em, h4 em { font-style: normal !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0f2744 !important; }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stRadio label { color: rgba(255,255,255,0.8) !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] strong { color: #ffffff !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

    /* Fix invisible number inputs */
    input[type="number"] {
        color: #1a202c !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e0 !important;
        border-radius: 8px !important;
    }
    input[type="number"]:focus {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.15) !important;
    }

    /* Fix all text inputs */
    textarea {
        color: #1a202c !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e0 !important;
        border-radius: 8px !important;
    }
    textarea:focus {
        border-color: #0d9488 !important;
    }

    /* Form container — remove default grey background */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 1.8rem 2rem !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    }

    /* Submit button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #0d9488 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.7rem 1.5rem !important;
        box-shadow: 0 4px 16px rgba(13,148,136,0.3) !important;
    }
    .stFormSubmitButton > button:hover {
        box-shadow: 0 6px 22px rgba(13,148,136,0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* Severity blocks */
    .sev-block {
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0 1.2rem;
        border-left: 6px solid;
    }
    .sev-emergency { background: #fff1f2; border-color: #e11d48; }
    .sev-doctor    { background: #fff7ed; border-color: #ea580c; }
    .sev-monitor   { background: #fefce8; border-color: #ca8a04; }
    .sev-mild      { background: #f0fdf4; border-color: #16a34a; }
    .sev-info      { background: #eff6ff; border-color: #2563eb; }

    .sev-title { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.3rem; }
    .sev-emergency .sev-title { color: #be123c; }
    .sev-doctor    .sev-title { color: #c2410c; }
    .sev-monitor   .sev-title { color: #a16207; }
    .sev-mild      .sev-title { color: #15803d; }
    .sev-info      .sev-title { color: #1d4ed8; }

    .conf-pill {
        display: inline-block; border-radius: 999px;
        padding: 0.15rem 0.75rem; font-size: 0.75rem;
        font-weight: 600; background: rgba(0,0,0,0.06); color: #374151;
    }

    .action-normal {
        background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 10px;
        padding: 0.8rem 1rem; font-size: 0.95rem; color: #065f46;
        font-weight: 500; margin-top: 0.5rem;
    }
    .action-urgent {
        background: #fff1f2; border: 1px solid #fca5a5; border-radius: 10px;
        padding: 0.8rem 1rem; font-size: 0.95rem; color: #991b1b;
        font-weight: 600; margin-top: 0.5rem;
    }

    .ev-item {
        background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 0.85rem 1rem; margin-bottom: 0.7rem;
    }
    .ev-source { font-weight: 700; font-size: 0.88rem; color: #1e3a5f; }
    .ev-topic  { font-size: 0.76rem; color: #6b7280; margin: 0.15rem 0 0.4rem; }
    .ev-text   { font-size: 0.88rem; line-height: 1.65; color: #374151; }

    .flag-chip {
        display: inline-block; background: #fff1f2; border: 1px solid #fca5a5;
        color: #b91c1c; border-radius: 999px; padding: 0.2rem 0.7rem;
        font-size: 0.78rem; font-weight: 600; margin: 0.15rem 0.1rem;
    }

    .res-head {
        font-size: 0.7rem; font-weight: 700; letter-spacing: 1.1px;
        text-transform: uppercase; color: #6b7280; margin: 1.1rem 0 0.3rem;
    }

    .disc-box {
        background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px;
        padding: 0.85rem 1rem; font-size: 0.85rem; color: #78350f; line-height: 1.65;
    }

    .badges { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.4rem 0 1.4rem; }
    .badge {
        background: #dbeafe; color: #1d4ed8; border-radius: 999px;
        padding: 0.25rem 0.8rem; font-size: 0.75rem; font-weight: 600;
    }

    .stat-chip {
        background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14);
        border-radius: 8px; padding: 0.5rem 0.8rem; margin-bottom: 0.4rem;
        font-size: 0.82rem; color: rgba(255,255,255,0.78) !important; display: block;
    }

    /* Label color for inputs inside form */
    [data-testid="stForm"] label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }

    /* Checkbox label */
    [data-testid="stForm"] .stCheckbox label {
        color: #374151 !important;
        font-weight: 400 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def severity_meta(severity: Severity):
    return {
        Severity.EMERGENCY:      ("🚨", "sev-emergency", "Emergency"),
        Severity.SEE_DOCTOR:     ("⚠️",  "sev-doctor",    "See a Doctor"),
        Severity.MONITOR:        ("📋", "sev-monitor",   "Monitor at Home"),
        Severity.MILD:           ("✅", "sev-mild",      "Mild — No Immediate Concern"),
        Severity.NEED_MORE_INFO: ("❓", "sev-info",      "Need More Information"),
    }.get(severity, ("🔵", "sev-info", "Unknown"))


def render_result(output):
    emoji, css_class, label = severity_meta(output.severity)
    pct = int(output.confidence * 100)
    is_urgent = output.severity in (Severity.EMERGENCY, Severity.SEE_DOCTOR)

    st.markdown(
        f"""
        <div class="sev-block {css_class}">
            <div class="sev-title">{emoji}&nbsp; {label}</div>
            <span class="conf-pill">Confidence: {pct}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="res-head">What This Means</div>', unsafe_allow_html=True)
    st.write(output.summary)

    st.markdown('<div class="res-head">Recommended Action</div>', unsafe_allow_html=True)
    box_class = "action-urgent" if is_urgent else "action-normal"
    st.markdown(f'<div class="{box_class}">{output.recommended_action}</div>', unsafe_allow_html=True)

    if output.follow_up_question:
        st.markdown('<div class="res-head">One More Thing</div>', unsafe_allow_html=True)
        st.markdown(f"*{output.follow_up_question}*")

    if output.red_flags:
        st.markdown('<div class="res-head">Red Flags Detected</div>', unsafe_allow_html=True)
        chips = "".join(f'<span class="flag-chip">{f}</span>' for f in output.red_flags)
        st.markdown(chips, unsafe_allow_html=True)

    st.divider()

    with st.expander("📚 Medical Evidence Reviewed"):
        if output.retrieved_evidence:
            for i, ev in enumerate(output.retrieved_evidence, 1):
                link = (
                    f' &nbsp;·&nbsp; <a href="{ev.source_url}" target="_blank" '
                    f'style="color:#0d9488;font-size:0.76rem;">View source ↗</a>'
                ) if ev.source_url else ""
                st.markdown(
                    f"""<div class="ev-item">
                        <div class="ev-source">{i}. {ev.source_name}{link}</div>
                        <div class="ev-topic">{ev.section_title}</div>
                        <div class="ev-text">{ev.excerpt}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.write("No specific guidance matched this description.")

    with st.expander("⚕️ Medical Disclaimer"):
        st.markdown(
            f'<div class="disc-box">{output.medical_disclaimer}<br><br>'
            '<strong>This is not a medical diagnosis.</strong> A qualified pediatrician must evaluate your child.<br><br>'
            '<strong>Trust your instincts.</strong> If you feel your child needs immediate attention, seek it without delay.</div>',
            unsafe_allow_html=True,
        )

    with st.expander("🔍 Technical Details"):
        st.json({
            "language": output.language.value,
            "severity": output.severity.value,
            "confidence": float(output.confidence),
            "extracted_symptoms": output.extracted_symptoms,
            "red_flags_detected": output.red_flags,
            "reasoning": output.reasoning,
        })


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## 🏥 PediTriage")
        st.caption("Pediatric Symptom Triage Assistant")
        st.divider()

        st.markdown("**Language**")
        language_choice = st.radio(
            "Language",
            ["Auto-detect", "English", "العربية"],
            index=0,
            label_visibility="collapsed",
        )
        language_map = {
            "Auto-detect": None,
            "English": Language.EN,
            "العربية": Language.AR,
        }

        st.divider()
        st.markdown("**About This Tool**")
        for chip in [
            "📋 4-level urgency classification",
            "🔍 Transparent reasoning",
            "📚 Medical evidence shown",
            "🌐 English & Arabic support",
        ]:
            st.markdown(f'<div class="stat-chip">{chip}</div>', unsafe_allow_html=True)

        st.divider()
        st.caption("Not a diagnostic tool. Always consult a qualified pediatrician.")

    # Hero
    st.title("🏥 Pediatric Safety Triage")
    st.markdown("Helps parents understand how urgent their child's symptoms are. **Not a diagnosis tool.**")
    st.markdown(
        '<div class="badges">'
        '<span class="badge">4-Level Urgency Scale</span>'
        '<span class="badge">Evidence-Backed</span>'
        '<span class="badge">Bilingual</span>'
        '<span class="badge">Not a Diagnosis</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Form
    with st.form("triage_form"):
        st.markdown("#### Child Details")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            age = st.number_input("Age (years)", min_value=0, max_value=18, value=None)
            age_months = int(age * 12) if age is not None else None

        with col2:
            temperature = st.number_input(
                "Temperature (optional)", min_value=95.0, max_value=107.0, value=None
            )

        with col3:
            temp_unit = None
            if temperature is not None:
                st.write("")
                temp_unit_choice = st.radio("Unit", ["°F", "°C"], horizontal=True)
                temp_unit = "F" if "°F" in temp_unit_choice else "C"

        st.divider()
        st.markdown("#### Red Flags")
        st.caption("Check all that apply")

        red_flag_options = [
            "Difficulty breathing", "Blue lips or tongue", "Severe pain",
            "Seizure or unresponsive", "High fever (104°F / 40°C+)",
            "Purple or non-blanching rash", "Stiff neck", "Excessive bleeding",
            "Severe dehydration", "None of the above",
        ]

        red_flags_selected = []
        c1, c2 = st.columns(2)
        for i, flag in enumerate(red_flag_options):
            if (c1 if i % 2 == 0 else c2).checkbox(flag, key=f"rf_{i}"):
                red_flags_selected.append(flag)

        st.divider()
        st.markdown("#### Describe the Symptoms")
        symptom_text = st.text_area(
            "Describe symptoms",
            placeholder=(
                "Example: My 3-year-old has had a fever of 101°F for 2 days, "
                "mild cough, still eating and drinking. No other concerns."
            ),
            height=130,
            label_visibility="collapsed",
        )

        st.write("")
        submitted = st.form_submit_button(
            "Assess Urgency", use_container_width=True, type="primary"
        )

    # Result
    if submitted:
        if not symptom_text.strip():
            st.error("Please describe the symptoms before submitting.")
            return

        with st.spinner("Analyzing symptoms and retrieving medical guidance…"):
            try:
                request = TriageRequest(
                    language=language_map[language_choice],
                    child_age_months=age_months,
                    temperature=temperature,
                    temperature_unit="F" if temp_unit == "F" else "C" if temp_unit == "C" else None,
                    symptom_description=symptom_text,
                    red_flags_reported=red_flags_selected,
                )
                result = run_triage(request)
                st.success("Assessment complete.")
                st.divider()
                render_result(result)

                with st.expander("📋 Session Log"):
                    st.json({
                        "timestamp": datetime.now().isoformat(),
                        "language": result.language.value,
                        "severity": result.severity.value,
                        "confidence": float(result.confidence),
                        "symptoms_count": len(result.extracted_symptoms),
                        "red_flags_count": len(result.red_flags),
                    })

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
