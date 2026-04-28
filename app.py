"""
Streamlit UI for pediatric symptom triage.

Parents enter symptoms, get urgency assessment, and see medical guidance.
"""

import json
import streamlit as st
from datetime import datetime

from src.schema import Language, TriageRequest, Severity
from src.triage import run_triage


# Page configuration
st.set_page_config(
    page_title="Pediatric Safety Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .severity-emergency {
        background-color: #fee;
        border-left: 5px solid #d32f2f;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .severity-see-doctor {
        background-color: #fff3e0;
        border-left: 5px solid #f57c00;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .severity-monitor {
        background-color: #fff8e1;
        border-left: 5px solid #fbc02d;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .severity-mild {
        background-color: #e8f5e9;
        border-left: 5px solid #388e3c;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .severity-need-more {
        background-color: #e3f2fd;
        border-left: 5px solid #1976d2;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .evidence-box {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 0.9em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def severity_to_emoji(severity: Severity) -> str:
    """Map severity to emoji."""
    mapping = {
        Severity.EMERGENCY: "🚨",
        Severity.SEE_DOCTOR: "⚠️",
        Severity.MONITOR: "📊",
        Severity.MILD: "✅",
        Severity.NEED_MORE_INFO: "❓",
    }
    return mapping.get(severity, "")


def severity_to_css_class(severity: Severity) -> str:
    """Map severity to CSS class."""
    mapping = {
        Severity.EMERGENCY: "severity-emergency",
        Severity.SEE_DOCTOR: "severity-see-doctor",
        Severity.MONITOR: "severity-monitor",
        Severity.MILD: "severity-mild",
        Severity.NEED_MORE_INFO: "severity-need-more",
    }
    return mapping.get(severity, "severity-mild")


def render_result(output):
    """Render triage result."""
    emoji = severity_to_emoji(output.severity)
    css_class = severity_to_css_class(output.severity)

    # Main result box
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
    st.markdown(
        f"### {emoji} Assessment: **{output.severity.value.upper()}**\n\n"
        f"Confidence: {int(output.confidence * 100)}%"
    )

    st.markdown("---")

    # Summary
    st.markdown("#### What This Means")
    st.write(output.summary)

    # Recommended action
    st.markdown("#### What To Do Next")
    st.info(output.recommended_action)

    # Follow-up question if needed
    if output.follow_up_question:
        st.markdown("#### Tell Us More")
        st.write(f"*{output.follow_up_question}*")

    st.markdown("</div>", unsafe_allow_html=True)

    # Evidence (expandable)
    with st.expander("📚 Why This Assessment?"):
        if output.retrieved_evidence:
            st.markdown("**Medical guidance we reviewed:**")
            for i, evidence in enumerate(output.retrieved_evidence, 1):
                st.markdown(f"**{i}. {evidence.source_name}**")
                st.write(f"*Topic: {evidence.section_title}*")
                st.write(evidence.excerpt)
                if evidence.source_url:
                    st.caption(f"[Read more]({evidence.source_url})")
                st.divider()
        else:
            st.write("No specific medical guidance matched this symptom description.")

    # Safety info
    with st.expander("⚕️ Important Disclaimer"):
        st.warning(output.medical_disclaimer)
        st.markdown(
            """
            **This is not a medical diagnosis or treatment plan.**
            
            This system is designed to help parents understand urgency, not to diagnose.
            A pediatrician or healthcare provider must evaluate your child for diagnosis and treatment.
            
            **Always trust your instincts.** If you believe your child needs medical attention, seek it immediately.
            """
        )

    # Transparency
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


def main():
    """Main Streamlit app."""
    st.title("🏥 Pediatric Safety Triage")
    st.markdown(
        """
        Helps parents understand urgency when a child has symptoms.
        **Not a diagnosis tool.** Guides parents to medical professionals.
        """
    )

    st.divider()

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        language_choice = st.radio(
            "Language / اللغة",
            ["Auto-detect", "English", "العربية"],
            index=0,
        )

        language_map = {
            "Auto-detect": None,
            "English": Language.EN,
            "العربية": Language.AR,
        }

        st.divider()
        st.markdown(
            """
            ### About This Tool
            
            This is a **safety-first triage assistant** for parents of Mumzworld.
            
            **What it does:**
            - Accepts symptom descriptions
            - Classifies urgency (mild, monitor, see-doctor, emergency)
            - Explains reasoning
            - Shows supporting evidence
            - Refuses to diagnose
            
            **What it doesn't do:**
            - Provide medical diagnosis
            - Replace doctor visits
            - Guarantee outcomes
            
            **When in doubt, contact your doctor.**
            """
        )

    st.divider()

    # Input form
    st.header("👧 Tell Us About Your Child's Symptoms")

    with st.form("triage_form"):
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Child's age",
                min_value=0,
                max_value=18,
                value=None,
                help="Age in years",
            )
            age_months = int(age * 12) if age is not None else None

        with col2:
            temperature = st.number_input(
                "Temperature (if known)",
                min_value=95.0,
                max_value=107.0,
                value=None,
                help="Fahrenheit or Celsius",
            )
            temp_unit = None
            if temperature is not None:
                temp_unit_choice = st.radio(
                    "Temperature unit",
                    ["°F", "°C"],
                    horizontal=True,
                    index=0,
                )
                temp_unit = "F" if "°F" in temp_unit_choice else "C"

        st.markdown("---")

        # Red flag checkboxes
        st.subheader("🚩 Check Any Red Flags You Notice")
        col1, col2 = st.columns(2)

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
        for i, flag in enumerate(red_flag_options):
            col = col1 if i % 2 == 0 else col2
            if col.checkbox(flag):
                red_flags_selected.append(flag)

        st.markdown("---")

        # Symptom description
        st.subheader("📝 Describe the Symptoms")
        symptom_text = st.text_area(
            "Tell us what symptoms your child has",
            placeholder="Example: My 3-year-old has had a fever of 101°F for 2 days, mild cough, and is still eating and drinking. No other concerns.",
            height=120,
        )

        st.divider()

        # Submit button
        submitted = st.form_submit_button(
            "🔍 Assess Urgency",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not symptom_text.strip():
            st.error("Please describe the symptoms.")
            return

        with st.spinner("Analyzing symptoms and retrieving medical guidance..."):
            try:
                # Create request
                request = TriageRequest(
                    language=language_map[language_choice],
                    child_age_months=age_months,
                    temperature=temperature,
                    temperature_unit="F" if temp_unit == "F" else "C" if temp_unit == "C" else None,
                    symptom_description=symptom_text,
                    red_flags_reported=red_flags_selected,
                )

                # Run triage
                result = run_triage(request)

                # Display result
                st.success("Assessment complete.")
                st.divider()

                render_result(result)

                # Log entry (for debugging)
                st.divider()
                with st.expander("📋 Log Entry"):
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "language": result.language.value,
                        "severity": result.severity.value,
                        "confidence": float(result.confidence),
                        "symptoms_count": len(result.extracted_symptoms),
                        "red_flags_count": len(result.red_flags),
                    }
                    st.json(log_entry)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
