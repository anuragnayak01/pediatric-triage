# Pediatric Symptom Triage With Hard Safety Guardrails - Project Flow

## Recommended Project Flow

The best version of this project should be a bilingual pediatric urgency-routing assistant, not a diagnosis tool.

The system should take a parent's symptom description in English or Arabic, retrieve relevant pediatric safety guidance, classify urgency, validate structured output, apply hard safety rules, and return a safe parent-facing response.

## Level 1: Parent Input

The parent should provide:

- Child's age.
- Symptoms.
- Duration.
- Temperature, if available.
- Behavior changes.
- Feeding or drinking status.
- Urination or wet diapers.
- Breathing issues.
- Rash, seizure, dehydration, severe pain, or alertness changes.

The UI should not only have a free-text box. It should also ask for key structured details because pediatric triage depends heavily on age, fever, breathing, hydration, and consciousness.

Recommended input fields:

- `Child age`
- `Temperature`
- `Symptoms description`
- `Duration`
- `Language: English / Arabic / Auto`
- Optional red flag checkboxes:
  - Breathing difficulty.
  - Blue lips.
  - Seizure.
  - Hard to wake.
  - No urine or dry mouth.
  - Stiff neck.
  - Severe pain.
  - Rash.

## Level 2: Language Handling

The system must work in both English and Arabic.

Best flow:

1. Detect whether input is English, Arabic, or mixed.
2. Preserve the original language.
3. For RAG retrieval, either use multilingual retrieval or translate Arabic internally to English for retrieval.
4. Generate the final response in the parent's language.
5. Ensure Arabic output is natural Arabic, not literal translation.

For mixed Arabic-English input, the system should still work. Example:

```text
My baby has 39 C fever and is crying بدون دموع
```

The system should understand both parts and detect dehydration risk.

## Level 3: RAG Knowledge Base

RAG should retrieve from curated pediatric safety guidance, not random web data.

The knowledge base should be chunked by clinical scenario, not arbitrary token size.

Best chunk categories:

- Age-specific fever rules.
- Infant fever rules.
- Emergency breathing red flags.
- Seizure and consciousness red flags.
- Dehydration signs.
- Vomiting and diarrhea thresholds.
- Rash and stiff neck warnings.
- Severe pain and trauma.
- Home monitoring guidance.
- When to call a pediatrician.
- When to go to emergency care.
- Medication safety warnings.

Each retrieved chunk should include:

- Source name.
- Topic.
- Severity relevance.
- Exact rule or guidance.
- Source URL.

The RAG output should not be hidden. The UI should show a "Why this assessment?" section with retrieved evidence.

## Level 4: Severity Classification

The system should classify into:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`
- optionally `abstain` or `need-more-info`

Including `abstain` internally is recommended, even if the final displayed level is "Need more information."

## Severity Level: Mild

Use this when symptoms are low-risk and no red flags are present.

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

Parent response should say:

- Monitor at home.
- Provide comfort.
- Keep fluids.
- Watch for red flags.
- Contact a doctor if symptoms worsen.

Even here, avoid diagnosis. Do not say "this is just a cold." Say "this sounds lower urgency based on the information provided."

## Severity Level: Monitor

Use this when symptoms are not clearly emergency-level but need close watching, or when details are incomplete.

Examples:

- Fever without enough age or duration details.
- Vomiting but child can drink.
- Mild diarrhea.
- Limited rash without red flags.
- Ear pain.
- Vague symptoms like "not feeling well."
- Parent gives incomplete information.

This level is important for uncertainty handling.

The system should say:

- "I don't have enough information to be certain."
- "Monitor closely."
- "Contact a doctor if symptoms persist, worsen, or red flags appear."
- Ask focused follow-up questions.

This level should still include a disclaimer.

## Severity Level: See-Doctor

Use this when the child should be evaluated by a pediatrician or urgent care.

Examples:

- Baby under 3 months with fever of 100.4°F / 38°C or higher.
- Infant 3-12 months with high fever.
- Fever lasting more than 24 hours in a child under 2.
- Fever lasting more than 3 days in an older child.
- Signs of dehydration:
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

The system must:

- Refuse diagnosis.
- Tell the parent to contact a pediatrician or urgent care.
- Show retrieved guideline evidence.
- Include confidence and uncertainty.
- Avoid giving medication dosing unless carefully sourced and allowed. Safer default: avoid dosage completely.

## Severity Level: Emergency

Use this when immediate emergency care may be needed.

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

The system must be direct:

- "Seek emergency care now."
- "Call local emergency services."
- "I cannot diagnose this."
- "This may be urgent based on the symptoms described."

No long explanation should delay the emergency instruction.

## Level 5: Structured Output

The model should return strict structured output before anything is shown in the UI.

Recommended fields:

- `language`
- `patient_age_months`
- `temperature`
- `extracted_symptoms`
- `duration`
- `red_flags`
- `retrieved_evidence`
- `severity`
- `confidence`
- `uncertainty_flag`
- `diagnosis_refusal`
- `escalation_required`
- `safety_rationale`
- `parent_instructions`
- `follow_up_questions`
- `disclaimer`

Validation rules:

- Severity must be one of the fixed labels.
- Confidence must be between 0 and 1.
- Red flags must be a list.
- Retrieved evidence must not be empty for medical claims.
- If age is missing and fever is present, uncertainty must be true.
- If severity is `see-doctor` or `emergency`, escalation must be true.
- If severity is `monitor`, `see-doctor`, or `emergency`, diagnosis refusal must be true.
- Empty strings should not be allowed.
- Malformed JSON should fail visibly.

## Level 6: Safety Guardrails

This is the most important part of the system.

The system should have two layers:

### Model Layer

The model reads input plus retrieved context and proposes structured output.

### Hard Safety Layer

After model output, deterministic safety checks override unsafe answers.

Examples:

- If child is under 3 months and has fever >= 100.4°F / 38°C, force `see-doctor`.
- If blue lips or breathing difficulty appears, force `emergency`.
- If seizure or unresponsive appears, force `emergency`.
- If age is missing and fever is mentioned, force uncertainty and ask for age.
- If retrieved context is weak or irrelevant, abstain.
- If user asks for diagnosis, refuse.
- If user asks for dosage, avoid or defer to doctor.

This is what safety by design means: the model is not trusted alone.

## Level 7: Uncertainty Handling

Good uncertainty behavior should be visible.

The system should say "I don't know" or "I don't have enough information" when:

- Age is missing.
- Temperature is missing but fever is mentioned.
- Symptoms are vague.
- Input is out of scope.
- Retrieved evidence is insufficient.
- Model output contradicts safety rules.
- Parent asks for diagnosis.
- Parent asks something unrelated to triage.

Example response:

```text
I don't have enough information to safely classify this. Please share the child's age, temperature, symptom duration, breathing status, hydration, and alertness. If the child is hard to wake, struggling to breathe, has blue lips, or has a seizure, seek emergency care now.
```

This directly matches the assignment's uncertainty requirement.

## Level 8: Streamlit UI Flow

Streamlit is a good fit for this Data Science / AI technical assessment.

Recommended UI sections:

1. Safety banner:
   - "This is a triage assistant, not a diagnostic tool."
   - "For life-threatening symptoms, call emergency services."

2. Input panel:
   - Child age.
   - Temperature.
   - Symptom description.
   - Language selector.

3. Triage result:
   - Color-coded severity:
     - Green: mild.
     - Yellow: monitor.
     - Orange: see-doctor.
     - Red: emergency.
     - Gray: need more information.

4. Recommended action:
   - Short, direct bullets.

5. Why this assessment?
   - Retrieved guideline chunks.
   - Matched red flags.
   - Safety rationale.

6. Structured JSON output:
   - Collapsible section for evaluators.

7. Uncertainty section:
   - Missing details.
   - Follow-up questions.

8. Eval/demo examples:
   - Buttons for sample cases in English and Arabic.

## Level 9: Eval Design

The project needs at least 10 test cases. A stronger target is 15.

Include:

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
15. Retrieval noise case with irrelevant or contradictory context.

Each eval should check:

- Correct severity.
- Correct refusal.
- Correct escalation.
- Valid schema.
- Relevant retrieved evidence.
- No hallucinated facts.
- Natural Arabic output.
- Safe uncertainty behavior.

## Level 10: Demo Flow

The 3-minute Loom should show 5 cases:

1. Mild English case.
2. Emergency English case.
3. Arabic mild or monitor case.
4. Arabic emergency case.
5. Vague or adversarial case where the system says it does not know or refuses diagnosis.

The last case is essential because the assignment explicitly asks to show refusal or uncertainty.

## Best Final Positioning

The project should be described as:

> A bilingual pediatric urgency-routing assistant for parents, grounded in curated pediatric safety guidance, using RAG, structured output validation, and hard safety guardrails to avoid diagnosis and escalate uncertain or risky cases.

Do not call it:

> A pediatric diagnosis system.

The strongest version is not the one that answers everything. The strongest version is the one that safely refuses, escalates, and explains why.
