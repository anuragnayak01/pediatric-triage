# Schema and Safety Rules

## Purpose

This document defines the structured output contract and hard safety rules for the pediatric symptom triage assistant.

The assistant is not a diagnostic system. It is a bilingual pediatric urgency-routing assistant that classifies urgency, explains uncertainty, cites retrieved guidance, and escalates risky cases.

## Severity Labels

Allowed severity labels:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`
- `need-more-info`

The model must not invent additional labels.

## Structured Output Schema

The assistant must produce a structured object before any parent-facing response is displayed.

Recommended fields:

### `language`

Type:

- string

Allowed values:

- `en`
- `ar`

Meaning:

- Language of the final parent-facing response.

Validation:

- Required.
- Must be `en` or `ar`.

### `patient_age_months`

Type:

- integer or null

Meaning:

- Child's age in months.

Validation:

- Required.
- Must be `null` if age is not provided.
- Must be greater than or equal to 0 when provided.

### `temperature_value`

Type:

- number or null

Meaning:

- Reported temperature.

Validation:

- Required.
- Must be `null` if not provided.
- Must be biologically plausible when provided.

### `temperature_unit`

Type:

- string or null

Allowed values:

- `F`
- `C`
- `null`

Validation:

- Required.
- Must be `F`, `C`, or `null`.

### `duration`

Type:

- string or null

Meaning:

- Symptom duration as stated or inferred.

Validation:

- Required.
- Can be `null` if missing.

### `extracted_symptoms`

Type:

- list of strings

Meaning:

- Symptoms extracted from the parent input.

Validation:

- Required.
- Must be non-empty for in-scope medical inputs.
- Empty list allowed only for out-of-scope or unusable inputs.

### `red_flags`

Type:

- list of strings

Meaning:

- Emergency or escalation signs detected in the input.

Validation:

- Required.
- Must be a list.

### `retrieved_evidence`

Type:

- list of evidence objects

Each evidence object should include:

- `chunk_id`
- `source_name`
- `source_file`
- `page_start`
- `page_end`
- `section_title`
- `excerpt`
- `relevance_reason`

Validation:

- Required.
- Must be non-empty when medical guidance is provided.
- Can be empty only when retrieval failed and the system is abstaining.

### `severity`

Type:

- string

Allowed values:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`
- `need-more-info`

Validation:

- Required.
- Must match one of the allowed labels.

### `confidence`

Type:

- number

Validation:

- Required.
- Must be between 0 and 1.
- Should be low when uncertainty is high.

### `uncertainty_flag`

Type:

- boolean

Meaning:

- Whether the system lacks enough information or evidence to classify confidently.

Validation:

- Required.
- Must be true when key details are missing in a risk-sensitive case.

### `missing_information`

Type:

- list of strings

Meaning:

- Important missing details needed for safer triage.

Examples:

- age
- temperature
- duration
- breathing status
- hydration status
- alertness

Validation:

- Required.
- Must be non-empty when `uncertainty_flag` is true due to missing details.

### `diagnosis_refusal`

Type:

- boolean

Meaning:

- Whether the response explicitly refuses to diagnose.

Validation:

- Required.
- Must be true for `monitor`, `see-doctor`, `emergency`, and `need-more-info`.

### `escalation_required`

Type:

- boolean

Meaning:

- Whether the parent should escalate to doctor, urgent care, or emergency services.

Validation:

- Required.
- Must be true for `see-doctor` and `emergency`.

### `safety_rationale`

Type:

- string

Meaning:

- Short explanation grounded in input and retrieved evidence.

Validation:

- Required.
- Must not be empty.
- Must not invent unsupported facts.

### `parent_instructions`

Type:

- list of strings

Meaning:

- Actionable instructions for the parent.

Validation:

- Required.
- Must be non-empty.
- Must not include diagnosis.
- Must not include medication dosing.

### `follow_up_questions`

Type:

- list of strings

Meaning:

- Focused questions to reduce uncertainty.

Validation:

- Required.
- Must be non-empty when `uncertainty_flag` is true.

### `disclaimer`

Type:

- string

Meaning:

- Medical safety disclaimer.

Validation:

- Required.
- Must be non-empty.
- Must clearly state that this is not a diagnosis.

## General Validation Rules

- No malformed JSON.
- No empty strings used to pass validation.
- No unsupported medical claims.
- No medication dosage.
- No diagnosis.
- No invented citations.
- Every medical recommendation should be supported by retrieved evidence or a hard safety rule.
- If validation fails, return a safe fallback response.

## Hard Safety Overrides

Hard safety overrides run after model output and before display.

The model is not the final authority.

### Emergency Overrides

Force `emergency` if any of the following are detected:

- Trouble breathing.
- Stopped breathing.
- Blue lips, tongue, or nails.
- Choking.
- Seizure.
- Unresponsive child.
- Child cannot be awakened.
- Severe allergic reaction.
- Heavy bleeding that cannot be stopped.
- Severe burns.
- Neck or spine injury.
- Coughing blood.
- Vomiting blood.
- Poisoning.
- Severe dehydration with lethargy.

Required emergency behavior:

- `severity = emergency`
- `escalation_required = true`
- `diagnosis_refusal = true`
- Direct instruction to seek emergency care now.

### See-Doctor Overrides

Force at least `see-doctor` if any of the following are detected:

- Baby under 3 months with fever >= 100.4°F / 38°C.
- Infant with high fever.
- Fever lasting more than 24 hours in a child under 2.
- Fever lasting more than 3 days in an older child.
- No wet diapers for 8-10 hours.
- Crying without tears.
- Dry mouth with reduced intake.
- Sunken soft spot.
- Persistent vomiting.
- Not keeping liquids down.
- Rash that blisters or looks infected.
- Fever with concerning rash.
- Severe ear pain.
- Severe sore throat.
- Stiff neck unless emergency signs are present.

Required see-doctor behavior:

- `severity = see-doctor`
- `escalation_required = true`
- `diagnosis_refusal = true`
- Recommend contacting pediatrician, urgent care, or local medical service.

### Need-More-Info Overrides

Force `need-more-info` or uncertainty when:

- Fever is mentioned but age is missing.
- Fever is mentioned but temperature is missing and severity cannot be inferred.
- Parent says symptoms are serious but gives no details.
- Input is too vague to classify.
- Retrieved evidence is weak, irrelevant, or missing.
- The model output contradicts retrieved evidence.
- The input is out of scope.

Required behavior:

- `uncertainty_flag = true`
- `diagnosis_refusal = true`
- Ask focused follow-up questions.
- Include emergency red flag warning.

## Refusal Rules

The assistant must refuse:

- Diagnosis requests.
- Requests to confirm that symptoms are harmless.
- Requests to ignore safety rules.
- Medication dosage requests.
- Treatment plans beyond general safe guidance.
- Out-of-scope medical questions not related to urgency routing.

Safe refusal pattern:

```text
I cannot diagnose this or confirm that it is harmless. Based on the information provided, the safest next step is...
```

## Uncertainty Rules

The assistant should explicitly say it does not know or does not have enough information when:

- Age is missing in a fever case.
- Temperature is missing in a high-fever case.
- Duration is missing for persistent symptoms.
- Hydration status is unknown in vomiting/diarrhea cases.
- Breathing status is unclear in respiratory cases.
- Alertness is unclear in severe or vague cases.
- Retrieval evidence is insufficient.

Uncertainty is a feature, not a failure.

## Multilingual Rules

The assistant must support:

- English input and output.
- Arabic input and output.
- Mixed English-Arabic input.

Rules:

- Final parent-facing response should match the selected or detected language.
- Arabic should be natural and parent-friendly.
- Arabic should not read like literal translation.
- Safety behavior must be identical across English and Arabic.
- Severity labels can remain controlled internally, but displayed labels may be localized.

## Parent-Facing Tone

The response should be:

- Calm.
- Direct.
- Shorter for emergency cases.
- Clear about uncertainty.
- Clear about next action.
- Never falsely reassuring.

Emergency responses should prioritize action over explanation.

## Safe Fallback Response

Use safe fallback if:

- JSON validation fails.
- Model output is malformed.
- Retrieval fails.
- The system detects contradiction.
- The model gives diagnosis or unsafe advice.

Fallback behavior:

- State that the system cannot safely classify.
- Ask for age, temperature, symptoms, duration, breathing, hydration, and alertness.
- Warn that breathing difficulty, blue lips, seizure, unresponsiveness, or severe dehydration should receive emergency care.
- Refuse diagnosis.

## README Requirements

The README should document:

- The schema.
- Validation rules.
- Safety overrides.
- Refusal rules.
- Uncertainty behavior.
- Why model output is not trusted directly.
- Examples of safe fallback.
