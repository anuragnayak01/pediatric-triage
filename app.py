"""
Streamlit UI for pediatric symptom triage.

Parents enter symptoms, get urgency assessment, and see medical guidance.
"""

import json
import streamlit as st
from datetime import datetime

from src.schema import Language, TriageRequest, Severity
from src.triage import run_triage


# ─── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PediTriage · Pediatric Symptom Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── Root variables ── */
    :root {
        --navy:       #0b1a2e;
        --teal:       #0d9488;
        --teal-light: #ccfbf1;
        --slate:      #1e3a5f;
        --cream:      #f8f6f1;
        --white:      #ffffff;
        --text-main:  #1a2a3a;
        --text-muted: #5a7184;

        --emergency-bg:  #fff1f2;
        --emergency-bdr: #e11d48;
        --doctor-bg:     #fff7ed;
        --doctor-bdr:    #ea580c;
        --monitor-bg:    #fefce8;
        --monitor-bdr:   #ca8a04;
        --mild-bg:       #f0fdf4;
        --mild-bdr:      #16a34a;
        --info-bg:       #eff6ff;
        --info-bdr:      #2563eb;
    }

    /* ── Global resets ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-main);
    }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(160deg, #0b1a2e 0%, #0f2744 40%, #0b2640 100%);
        min-height: 100vh;
    }

    /* ── Main content wrapper ── */
    .block-container {
        padding: 2rem 3rem 4rem !important;
        max-width: 1100px !important;
    }

    /* ── Hero header ── */
    .hero-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        margin-bottom: 1rem;
    }
    .hero-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 3rem;
        color: var(--white);
        letter-spacing: -0.5px;
        margin: 0 0 0.5rem;
        line-height: 1.15;
    }
    .hero-header h1 span {
        color: #2dd4bf;
    }
    .hero-tagline {
        font-size: 1.05rem;
        color: rgba(255,255,255,0.6);
        font-weight: 300;
        letter-spacing: 0.3px;
    }

    /* ── Pill badges ── */
    .badge-row {
        display: flex;
        justify-content: center;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin: 1rem 0 2rem;
    }
    .badge {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.75);
        border-radius: 999px;
        padding: 0.3rem 0.9rem;
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* ── Cards ── */
    .card {
        background: var(--white);
        border-radius: 16px;
        padding: 2rem 2.2rem;
        box-shadow: 0 4px 30px rgba(0,0,0,0.18);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .card-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.35rem;
        color: var(--navy);
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .card-subtitle {
        color: var(--text-muted);
        font-size: 0.85rem;
        margin-bottom: 1.2rem;
    }

    /* ── Form inputs override ── */
    .stTextArea textarea, .stNumberInput input {
        border-radius: 10px !important;
        border: 1.5px solid #d1d5db !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        transition: border-color 0.2s;
    }
    .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.12) !important;
    }

    /* ── Checkbox ── */
    .stCheckbox label {
        font-size: 0.9rem !important;
        color: var(--text-main) !important;
    }

    /* ── Submit button ── */
    .stFormSubmitButton button {
        background: linear-gradient(135deg, #0d9488, #0369a1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        letter-spacing: 0.4px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 20px rgba(13,148,136,0.35) !important;
    }
    .stFormSubmitButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(13,148,136,0.45) !important;
    }

    /* ── Section label ── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: var(--teal);
        margin-bottom: 0.4rem;
    }

    /* ── Severity result cards ── */
    .severity-block {
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin: 0.5rem 0 1.2rem;
        border-left: 5px solid;
        animation: fadeIn 0.4s ease;
    }
    .severity-block h2 {
        font-family: 'DM Serif Display', serif;
        font-size: 1.6rem;
        margin: 0 0 0.2rem;
    }
    .severity-block .confidence-pill {
        display: inline-block;
        background: rgba(0,0,0,0.07);
        border-radius: 999px;
        padding: 0.15rem 0.7rem;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .sv-emergency  { background: var(--emergency-bg); border-color: var(--emergency-bdr); }
    .sv-doctor     { background: var(--doctor-bg);    border-color: var(--doctor-bdr);    }
    .sv-monitor    { background: var(--monitor-bg);   border-color: var(--monitor-bdr);   }
    .sv-mild       { background: var(--mild-bg);      border-color: var(--mild-bdr);      }
    .sv-info       { background: var(--info-bg);      border-color: var(--info-bdr);      }

    .sv-emergency h2  { color: var(--emergency-bdr); }
    .sv-doctor    h2  { color: var(--doctor-bdr);    }
    .sv-monitor   h2  { color: var(--monitor-bdr);   }
    .sv-mild      h2  { color: var(--mild-bdr);      }
    .sv-info      h2  { color: var(--info-bdr);      }

    /* ── Result section header ── */
    .result-section-head {
        font-family: 'DM Serif Display', serif;
        font-size: 1.05rem;
        color: var(--navy);
        margin: 1.2rem 0 0.35rem;
    }
    .result-body-text {
        font-size: 0.96rem;
        line-height: 1.7;
        color: var(--text-main);
    }

    /* ── Action box ── */
    .action-box {
        background: #ecfdf5;
        border: 1px solid #6ee7b7;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        font-size: 0.95rem;
        color: #065f46;
        font-weight: 500;
    }
    .action-box.urgent {
        background: #fff1f2;
        border-color: #fca5a5;
        color: #991b1b;
    }

    /* ── Evidence card ── */
    .evidence-item {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.75rem;
    }
    .evidence-source {
        font-weight: 600;
        font-size: 0.88rem;
        color: var(--slate);
    }
    .evidence-topic {
        font-size: 0.78rem;
        color: var(--text-muted);
        margin: 0.15rem 0 0.5rem;
    }
    .evidence-excerpt {
        font-size: 0.88rem;
        line-height: 1.6;
        color: var(--text-main);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0f2744 !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,0.82) !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--white) !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.9rem !important;
    }
    .sidebar-logo {
        font-family: 'DM Serif Display', serif;
        font-size: 1.4rem;
        color: white !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .sidebar-logo span {
        color: #2dd4bf !important;
    }
    .sidebar-stat {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.5rem;
        font-size: 0.82rem;
    }

    /* ── Divider ── */
    hr {
        border-color: rgba(255,255,255,0.08) !important;
    }

    /* ── Animations ── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.5s ease forwards; }

    /* ── Stagger for result cards ── */
    .card { animation: fadeIn 0.45s ease both; }
    .card:nth-child(2) { animation-delay: 0.05s; }
    .card:nth-child(3) { animation-delay: 0.10s; }
    .card:nth-child(4) { animation-delay: 0.15s; }

    /* ── Red flag chips ── */
    .flag-chip {
        display: inline-block;
        background: #fff1f2;
        border: 1px solid #fca5a5;
        color: #b91c1c;
        border-radius: 999px;
        padding: 0.2rem 0.7rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.15rem;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stExpander"] summary {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    /* ── Disclaimer ── */
    .disclaimer-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,220,100,0.3);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        font-size: 0.84rem;
        color: rgba(255,255,255,0.65);
        line-height: 1.65;
        margin-top: 0.5rem;
    }
    .disclaimer-box strong {
        color: rgba(255,255,255,0.88) !important;
    }

    /* ── Input label ── */
    .stTextArea label, .stNumberInput label, .stCheckbox label, .stRadio label {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    /* ── Form on white background ── */
    .form-wrap {
        background: var(--white);
        border-radius: 20px;
        padding: 2.2rem 2.4rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.25);
        margin-bottom: 1.5rem;
    }
    .form-wrap .stTextArea label,
    .form-wrap .stNumberInput label,
    .form-wrap .stCheckbox label,
    .form-wrap .stRadio label,
    .form-wrap p,
    .form-wrap span {
        color: var(--text-main) !important;
    }
    .form-wrap h3, .form-wrap h4 {
        color: var(--navy) !important;
    }

    /* ── Result wrapper ── */
    .result-card {
        background: var(--white);
        border-radius: 20px;
        padding: 2rem 2.4rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.25);
        margin-bottom: 1.5rem;
    }
    .result-card * {
        color: var(--text-main) !important;
    }
    .result-card h3 {
        color: var(--navy) !important;
    }

    /* stInfo / stWarning override inside result cards */
    .result-card .stAlert {
        background: var(--info-bg) !important;
        border-radius: 10px !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: var(--teal) !important;
    }

    /* Remove default Streamlit top padding */
    .css-18e3th9, .css-1d391kg { padding-top: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def severity_meta(severity: Severity):
    """Return (emoji, css_class, label) for a severity."""
    meta = {
        Severity.EMERGENCY:     ("🚨", "sv-emergency", "Emergency"),
        Severity.SEE_DOCTOR:    ("⚠️",  "sv-doctor",    "See a Doctor"),
        Severity.MONITOR:       ("📋", "sv-monitor",   "Monitor at Home"),
        Severity.MILD:          ("✅", "sv-mild",      "Mild – No Immediate Concern"),
        Severity.NEED_MORE_INFO:("❓", "sv-info",      "Need More Information"),
    }
    return meta.get(severity, ("🔵", "sv-info", "Unknown"))


def render_result(output):
    """Render triage result inside a white result card."""
    emoji, css_class, label = severity_meta(output.severity)
    confidence_pct = int(output.confidence * 100)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    # ── Severity block
    st.markdown(
        f"""
        <div class="severity-block {css_class}">
            <h2>{emoji} &nbsp;{label}</h2>
            <span class="confidence-pill">Confidence: {confidence_pct}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Summary
    st.markdown('<p class="result-section-head">What This Means</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="result-body-text">{output.summary}</p>', unsafe_allow_html=True)

    # ── Recommended action
    is_urgent = output.severity in (Severity.EMERGENCY, Severity.SEE_DOCTOR)
    action_class = "action-box urgent" if is_urgent else "action-box"
    st.markdown('<p class="result-section-head">Recommended Action</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="{action_class}">{output.recommended_action}</div>',
        unsafe_allow_html=True,
    )

    # ── Follow-up question
    if output.follow_up_question:
        st.markdown('<p class="result-section-head">One More Thing</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="result-body-text"><em>{output.follow_up_question}</em></p>',
            unsafe_allow_html=True,
        )

    # ── Red flags detected
    if output.red_flags:
        st.markdown('<p class="result-section-head">Red Flags Detected</p>', unsafe_allow_html=True)
        chips = "".join(f'<span class="flag-chip">⚑ {f}</span>' for f in output.red_flags)
        st.markdown(chips, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Evidence expander
    with st.expander("📚 Medical Evidence We Reviewed"):
        if output.retrieved_evidence:
            for i, ev in enumerate(output.retrieved_evidence, 1):
                url_html = f' · <a href="{ev.source_url}" target="_blank" style="color:#0d9488;font-size:0.78rem;">View source ↗</a>' if ev.source_url else ""
                st.markdown(
                    f"""
                    <div class="evidence-item">
                        <div class="evidence-source">{i}. {ev.source_name}{url_html}</div>
                        <div class="evidence-topic">{ev.section_title}</div>
                        <div class="evidence-excerpt">{ev.excerpt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.write("No specific medical guidance matched this symptom description.")

    # ── Disclaimer expander
    with st.expander("⚕️ Medical Disclaimer"):
        st.markdown(
            f"""
            <div class="disclaimer-box">
                {output.medical_disclaimer}<br><br>
                <strong>This is not a medical diagnosis.</strong> This tool is designed to help 
                parents understand urgency — not to diagnose or prescribe. A qualified pediatrician 
                must evaluate your child for any diagnosis and treatment plan.<br><br>
                <strong>Always trust your instincts.</strong> If you believe your child needs 
                immediate medical attention, seek it without delay.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Technical details expander
    with st.expander("🔍 Technical Details"):
        st.json(
            {
                "language": output.language.value,
                "severity": output.severity.value,
                "confidence": float(output.confidence),
                "extracted_symptoms": output.extracted_symptoms,
                "red_flags_detected": output.red_flags,
                "reasoning": output.reasoning,
            }
        )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Main Streamlit app."""

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">🏥 <span>Pedi</span>Triage</div>',
            unsafe_allow_html=True,
        )
        st.caption("Pediatric Symptom Triage Assistant")
        st.divider()

        st.markdown("**🌐 Language**")
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
        st.markdown(
            """
            <div class="sidebar-stat">📋 Classifies urgency into 4 levels</div>
            <div class="sidebar-stat">🔍 Explains reasoning transparently</div>
            <div class="sidebar-stat">📚 Shows supporting medical evidence</div>
            <div class="sidebar-stat">🌐 English & Arabic support</div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            '<div class="disclaimer-box" style="margin-top:0">Not a diagnostic tool. '
            'Always consult a qualified pediatrician for medical decisions.</div>',
            unsafe_allow_html=True,
        )

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-header">
            <h1>Pediatric <span>Safety</span> Triage</h1>
            <p class="hero-tagline">
                Understand urgency. Get clarity. Act with confidence.
            </p>
        </div>
        <div class="badge-row">
            <span class="badge">🚑 4-Level Urgency Scale</span>
            <span class="badge">🩺 Evidence-Backed Guidance</span>
            <span class="badge">🌐 Bilingual</span>
            <span class="badge">🔒 Not a Diagnosis</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Input Form ────────────────────────────────────────────────────────────
    st.markdown('<div class="form-wrap">', unsafe_allow_html=True)

    with st.form("triage_form"):

        # — Child details row
        st.markdown("#### 👧 Child Details")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            age = st.number_input(
                "Age (years)",
                min_value=0,
                max_value=18,
                value=None,
                help="Enter child's age in years",
            )
            age_months = int(age * 12) if age is not None else None

        with col2:
            temperature = st.number_input(
                "Temperature (optional)",
                min_value=95.0,
                max_value=107.0,
                value=None,
                help="Enter body temperature if known",
            )

        with col3:
            temp_unit = None
            if temperature is not None:
                st.markdown("<br>", unsafe_allow_html=True)
                temp_unit_choice = st.radio(
                    "Unit",
                    ["°F", "°C"],
                    horizontal=True,
                    index=0,
                )
                temp_unit = "F" if "°F" in temp_unit_choice else "C"

        st.divider()

        # — Red flags
        st.markdown("#### 🚩 Red Flags  *(check all that apply)*")

        red_flag_options = [
            "Difficulty breathing",
            "Blue lips or tongue",
            "Severe pain",
            "Seizure or unresponsive",
            "High fever (104°F / 40°C+)",
            "Purple or non-blanching rash",
            "Stiff neck",
            "Excessive bleeding",
            "Severe dehydration",
            "None of the above",
        ]

        red_flags_selected = []
        cols = st.columns(2)
        for i, flag in enumerate(red_flag_options):
            if cols[i % 2].checkbox(flag, key=f"flag_{i}"):
                red_flags_selected.append(flag)

        st.divider()

        # — Symptom description
        st.markdown("#### 📝 Describe the Symptoms")
        symptom_text = st.text_area(
            "Tell us what's going on",
            placeholder=(
                "Example: My 3-year-old has had a fever of 101°F for 2 days with a mild cough. "
                "She is still eating and drinking normally, and seems alert. No rash or other concerns."
            ),
            height=130,
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🔍  Assess Urgency",
            use_container_width=True,
            type="primary",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Result ────────────────────────────────────────────────────────────────
    if submitted:
        if not symptom_text.strip():
            st.error("⚠️ Please describe the symptoms before submitting.")
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

                st.success("✅ Assessment complete.", icon="✅")
                render_result(result)

                # Log entry
                with st.expander("📋 Session Log"):
                    st.json(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "language": result.language.value,
                            "severity": result.severity.value,
                            "confidence": float(result.confidence),
                            "symptoms_count": len(result.extracted_symptoms),
                            "red_flags_count": len(result.red_flags),
                        }
                    )

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
