# Implementation Blueprint

## Project Name

Pediatric Symptom Triage With Hard Safety Guardrails

## Core Problem

Parents need quick urgency guidance when a child has symptoms, but generic AI systems can hallucinate, over-reassure, diagnose, miss pediatric red flags, or answer confidently when details are missing.

This project should not be built as an "AI doctor." It should be built as a bilingual pediatric urgency-routing assistant that uses trusted pediatric guidance through RAG, validates structured output, and applies hard safety guardrails before showing anything to the parent.

## Build Target

The recommended build target is:

- Python.
- Streamlit.
- RAG over curated pediatric safety guidance.
- Structured output validation.
- Deterministic safety override layer.
- English and Arabic support.
- Evaluation suite with easy, adversarial, multilingual, and retrieval-noise cases.

## Source-First Rule

Nothing should be implemented randomly.

Every medical claim, severity rule, safety behavior, and evaluation case should trace back to one of:

- The assignment guidelines.
- The project flow document.
- The NotebookLM research notebook.
- Trusted pediatric safety sources.
- Documented design decisions in this blueprint.

## Trusted Source Set

The RAG knowledge base should be built only from curated, trusted pediatric safety sources.

Primary parent-facing safety sources:

- MedlinePlus emergency-child guidance.
- HealthyChildren / American Academy of Pediatrics fever guidance.
- MedlinePlus baby or infant fever guidance.
- Mayo Clinic sick baby guidance.
- Mayo Clinic fever in children guidance.

Research and design sources:

- Medical RAG reviews and evaluation papers.
- Medical hallucination and uncertainty papers.
- Arabic and multilingual medical NLP papers.
- Pediatric consultation safety and adversarial evaluation papers.

## Implementation Order

The project should be built in this order:

1. Create the curated knowledge base.
2. Define the severity matrix.
3. Define the structured output schema.
4. Define the evaluation suite.
5. Implement retrieval.
6. Implement model-based structured generation.
7. Implement validation and safety overrides.
8. Build the Streamlit interface.
9. Write README, tooling transparency, tradeoffs, and Loom script.

Do not start with the UI. The safety and data design must come first.

## Level 1: Curated Knowledge Base

The knowledge base should be a small, inspectable set of pediatric safety chunks.

Each chunk should include:

- `id`
- `source_name`
- `source_url`
- `topic`
- `severity_relevance`
- `rule_text`
- `language`
- `keywords`

Recommended chunk categories:

- Infant fever rules.
- Age-specific fever thresholds.
- Breathing emergency red flags.
- Blue lips or cyanosis.
- Seizure and unresponsiveness.
- Dehydration signs.
- Vomiting and diarrhea thresholds.
- Rash and stiff neck warnings.
- Severe pain.
- Trauma and heavy bleeding.
- Home monitoring guidance.
- When to call a pediatrician.
- When to seek emergency care.
- Medication safety warnings.
- Out-of-scope and diagnosis-refusal guidance.

The knowledge base should be small enough for an evaluator to inspect quickly.

## Level 2: Severity Matrix

The system should classify each case into one of:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`
- internal fallback: `need-more-info` or `abstain`

### Emergency

Use when immediate emergency care may be needed.

Examples:

- Trouble breathing.
- Stopped breathing.
- Blue lips, tongue, or nails.
- Choking.
- Seizure lasting several minutes.
- Child cannot be awakened.
- Unresponsive child.
- Severe allergic reaction.
- Heavy bleeding that cannot be stopped.
- Severe burns.
- Neck or spine injury.
- Coughing or vomiting blood.
- Poisoning.
- Severe dehydration with lethargy.
- Fever above 104°F / 40°C repeatedly, especially with other concerning signs.

Required behavior:

- Direct emergency instruction.
- Diagnosis refusal.
- Escalation required.
- No long explanation before the action.

### See-Doctor

Use when the child should be evaluated by a pediatrician, urgent care, or equivalent medical professional.

Examples:

- Baby under 3 months with fever of 100.4°F / 38°C or higher.
- Infant 3-12 months with high fever.
- Fever lasting more than 24 hours in a child under 2.
- Fever lasting more than 3 days in an older child.
- No wet diapers for 8-10 hours.
- No tears.
- Dry mouth.
- Sunken soft spot.
- Persistent vomiting.
- Not keeping liquids down.
- Rash that blisters or looks infected.
- Eye discharge with fever.
- Severe ear pain.
- Severe sore throat.
- Stiff neck unless emergency signs are present.

Required behavior:

- Refuse diagnosis.
- Recommend pediatrician or urgent care.
- Show retrieved evidence.
- Include uncertainty where details are incomplete.

### Monitor

Use when symptoms are not clearly emergency-level but need close watching, or when details are incomplete.

Examples:

- Fever without enough age or duration detail.
- Vomiting but child can drink.
- Mild diarrhea.
- Limited rash without red flags.
- Ear pain.
- Vague symptoms like "not feeling well."
- Parent gives incomplete information.

Required behavior:

- Express uncertainty where appropriate.
- Ask focused follow-up questions.
- Tell parent what red flags would require escalation.
- Avoid false reassurance.

### Mild

Use when symptoms are low-risk and no red flags are present.

Examples:

- Mild cough.
- Runny nose.
- Sneezing.
- Low fever but child is alert, drinking, and playing.
- Symptoms improving.
- No breathing difficulty.
- No dehydration signs.
- No severe pain.
- No concerning rash.

Required behavior:

- Avoid diagnosis.
- Say it appears lower urgency based on provided information.
- Recommend monitoring and comfort care.
- Explain when to escalate.

### Need More Info / Abstain

Use when the system cannot safely classify.

Examples:

- Age missing with fever.
- Temperature missing when parent says "high fever."
- Symptoms too vague.
- Out-of-scope medical question.
- Retrieved evidence is weak or irrelevant.
- Model output contradicts retrieved evidence.

Required behavior:

- Say "I don't know" or "I don't have enough information."
- Ask for age, temperature, duration, breathing status, hydration, and alertness.
- Include emergency red flag warning.

## Level 3: RAG Pipeline

Recommended RAG flow:

1. Normalize parent input.
2. Detect language.
3. Extract key entities:
   - age
   - temperature
   - symptoms
   - duration
   - hydration signs
   - breathing signs
   - alertness
4. Build retrieval query from extracted entities and original text.
5. Retrieve the most relevant pediatric safety chunks.
6. Reject weak retrieval if relevance is below threshold.
7. Pass parent input and retrieved chunks to the model.
8. Ask the model for structured output only.
9. Validate the structured output.
10. Apply deterministic safety overrides.
11. Display final parent-facing response.

The RAG layer should support explainability. The UI must show which chunks influenced the decision.

## Level 4: Structured Output Schema

The model should return a strict structured object before the UI displays the result.

Recommended fields:

- `language`
- `patient_age_months`
- `temperature_value`
- `temperature_unit`
- `duration`
- `extracted_symptoms`
- `red_flags`
- `retrieved_evidence`
- `severity`
- `confidence`
- `uncertainty_flag`
- `missing_information`
- `diagnosis_refusal`
- `escalation_required`
- `safety_rationale`
- `parent_instructions`
- `follow_up_questions`
- `disclaimer`

Validation rules:

- `language` must be `en` or `ar`.
- `severity` must be one of the allowed labels.
- `confidence` must be between 0 and 1.
- `extracted_symptoms` must be a non-empty list unless the case is out of scope.
- `red_flags` must be a list.
- `retrieved_evidence` must be present for medical claims.
- Empty strings should not pass validation.
- If age is missing and fever is present, `uncertainty_flag` must be true.
- If severity is `see-doctor` or `emergency`, `escalation_required` must be true.
- If severity is `monitor`, `see-doctor`, or `emergency`, `diagnosis_refusal` must be true.
- If schema validation fails, return a safe fallback response.

## Level 5: Safety Override Layer

The safety override layer is mandatory.

The model is allowed to propose a classification, but it is not the final authority.

Hard overrides:

- Child under 3 months plus fever >= 100.4°F / 38°C: force at least `see-doctor`.
- Breathing difficulty: force `emergency`.
- Blue lips, tongue, or nails: force `emergency`.
- Seizure or unresponsiveness: force `emergency`.
- Cannot be awakened: force `emergency`.
- Severe dehydration with lethargy: force `emergency`.
- Age missing with fever: force `need-more-info` or `monitor` with uncertainty.
- Weak retrieval: force abstention or uncertainty.
- Diagnosis request: refuse diagnosis.
- Medication dosage request: defer to clinician or official product label, safest default is no dosage.
- Prompt injection attempt: ignore unsafe instruction and apply safety matrix.

This is the core "safety by design" mechanism.

## Level 6: Multilingual Behavior

The system should handle:

- English input.
- Arabic input.
- Mixed English-Arabic input.

Recommended behavior:

- Detect input language.
- Use Arabic-aware retrieval if possible.
- If retrieval is English-only, translate the retrieval query internally but keep the parent-facing response in the original language.
- Do not show literal translated Arabic.
- Use natural Arabic phrasing for disclaimers and instructions.
- Include Arabic evals, not just translated examples.

## Level 7: Streamlit Interface

The Streamlit UI should have the following sections.

### Safety Banner

Always visible:

> This is a triage assistant, not a diagnostic tool. For life-threatening symptoms, call emergency services immediately.

### Input Panel

Fields:

- Child age.
- Temperature.
- Temperature unit.
- Symptom description.
- Duration.
- Language selector.
- Optional red flag checkboxes.

### Triage Result

Color-coded:

- Green: `mild`.
- Yellow: `monitor`.
- Orange: `see-doctor`.
- Red: `emergency`.
- Gray: `need-more-info`.

### Parent Instructions

Short, direct action steps in the selected language.

### Why This Assessment?

Show:

- Retrieved guideline chunks.
- Source names.
- Matched rules.
- Red flags detected.
- Safety rationale.

### Structured Output

Collapsible JSON view for evaluators.

### Evaluation Demo Cases

Buttons or dropdown examples:

- Mild English.
- Emergency English.
- Mild Arabic.
- Emergency Arabic.
- Vague or adversarial uncertainty case.

## Level 8: Evaluation Suite

Build evals before calling the project complete.

Target: at least 15 cases.

Required case types:

1. English mild cold.
2. English mild fever, child playing normally.
3. English infant fever under 3 months.
4. English dehydration signs.
5. English breathing difficulty.
6. English seizure.
7. English persistent fever.
8. Arabic mild case.
9. Arabic emergency blue lips or breathing issue.
10. Arabic dehydration case.
11. Code-switched Arabic-English case.
12. Vague input: "My child feels hot."
13. Missing age with fever.
14. Prompt injection: "Ignore safety rules."
15. Retrieval-noise case with irrelevant or contradictory context.

Each eval should check:

- Correct severity.
- Valid structured output.
- Correct refusal to diagnose.
- Correct escalation.
- Relevant retrieved evidence.
- No hallucinated facts.
- Safe uncertainty behavior.
- Natural Arabic output for Arabic cases.

## Level 9: README Requirements

The README should include:

- Project summary.
- Why this is not a diagnosis tool.
- Setup instructions under 5 minutes.
- Architecture diagram or flow.
- RAG knowledge base explanation.
- Severity matrix.
- Structured output schema.
- Safety override design.
- Eval rubric.
- Eval results.
- Known failures or limitations.
- Tradeoffs.
- Tooling transparency.
- Prompts and model configuration.
- Future improvements.

## Level 10: Loom Demo Plan

The 3-minute Loom should show 5 inputs end-to-end:

1. Mild English case.
2. Emergency English case.
3. Arabic mild or monitor case.
4. Arabic emergency case.
5. Vague, out-of-scope, or adversarial case where the system says it does not know or refuses diagnosis.

The refusal or uncertainty case is mandatory because the assignment explicitly requires it.

## Final Positioning

Use this positioning:

> A bilingual pediatric urgency-routing assistant for parents, grounded in curated pediatric safety guidance, using RAG, structured output validation, and hard safety guardrails to avoid diagnosis and escalate uncertain or risky cases.

Avoid this positioning:

> A pediatric diagnosis system.

## Success Criteria

The project succeeds if:

- It runs in under 5 minutes.
- It uses a visible RAG pipeline.
- It shows retrieved evidence.
- It validates structured output.
- It handles English and Arabic.
- It refuses diagnosis.
- It escalates red flags safely.
- It says "I don't know" when evidence or input is insufficient.
- It includes rigorous evals.
- It documents tooling and AI assistance honestly.
