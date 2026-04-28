# Pediatric Symptom Triage With Hard Safety Guardrails

## Project Understanding

This project is a pediatric symptom triage assistant for Mumzworld parents. A parent describes a child's symptoms in natural language, either in English or Arabic, and the system classifies the urgency level as one of:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`

The system is not a diagnostic tool. Its purpose is to help route urgency safely, explain uncertainty clearly, and guide parents toward medical help when needed.

## Core Idea

The assistant should understand a parent's symptom description, retrieve relevant pediatric safety guidance, and produce a structured triage result. It must refuse to diagnose and must escalate when the symptoms suggest moderate or serious concern.

The safest behavior is not to sound confident in uncertain cases. The system should know when to say:

> I don't know. Please contact your doctor.

## Why This Project Is Strong

This project is high-leverage because Mumzworld serves parents, and parents often need help deciding whether symptoms can be monitored or require medical attention.

It also maps well to the assessment guidelines because it demonstrates:

- RAG over medical safety guidance.
- Structured output with validation.
- Safety by design.
- Strong uncertainty handling.
- English and Arabic multilingual support.
- Rigorous evaluation with easy and adversarial test cases.

## Required Features

The system should support:

- Natural language symptom input from a parent.
- English and Arabic input.
- English and Arabic output.
- Retrieval over a curated pediatric safety knowledge base.
- Severity classification.
- Structured reasoning.
- Confidence score.
- Red flag detection.
- Recommended next action.
- Medical disclaimer.
- Explicit refusal to diagnose.
- Escalation when severity is moderate or higher.
- Clear uncertainty behavior for vague or unsupported inputs.

## Severity Labels

The system should classify each case into one of four severity levels:

### `mild`

Low-risk symptoms with no red flags. The system may suggest monitoring and basic comfort guidance, while still avoiding diagnosis.

### `monitor`

Symptoms are not immediately severe, but the parent should observe closely. This should also be used when the input is vague, incomplete, or unsupported.

### `see-doctor`

Symptoms suggest the child should be evaluated by a pediatrician or urgent care. The system must refuse diagnosis and escalate with a disclaimer.

### `emergency`

Symptoms suggest possible immediate danger, such as breathing difficulty, seizure, blue lips, unconsciousness, or severe dehydration. The system must recommend emergency care immediately.

## RAG Requirement

The project should use Retrieval-Augmented Generation over a small curated pediatric safety knowledge base.

The knowledge base may contain manually created or curated guidance snippets about:

- Breathing difficulty.
- Fever in infants.
- Persistent high fever.
- Seizures.
- Dehydration signs.
- Severe pain.
- Rash red flags.
- Vomiting and diarrhea.
- When to monitor.
- When to contact a doctor.
- When to seek emergency care.

The model should ground its output in retrieved context and should not invent facts outside the parent input or retrieved guidance.

## Structured Output Requirement

The system should return a strict structured output object. Suggested fields:

- `language`
- `severity`
- `confidence`
- `summary`
- `reasoning`
- `red_flags`
- `retrieved_evidence`
- `recommended_action`
- `disclaimer`
- `diagnosis_refusal`
- `escalation_required`
- `follow_up_questions`
- `uncertainty`

The output must validate against a schema. Invalid or malformed output should be handled explicitly.

## Safety Requirements

The assistant must:

- Never diagnose the child.
- Never claim certainty where the input is incomplete.
- Never provide medication dosage.
- Never replace a doctor, pediatrician, emergency service, or local medical advice.
- Escalate emergency red flags immediately.
- Escalate moderate or higher severity with a disclaimer.
- Say it does not know when the input is unsupported.
- Ask focused follow-up questions when useful.
- Avoid false reassurance.

## Multilingual Requirements

The system must work in both English and Arabic.

Arabic output should read naturally and not like literal machine translation. The assistant should preserve the same safety behavior in both languages.

The eval set should include both English and Arabic cases.

## Evaluation Requirements

The project should include at least 10 test cases with a mix of:

- Easy mild cases.
- Monitor cases.
- See-doctor cases.
- Emergency cases.
- Vague inputs.
- Out-of-scope inputs.
- Prompt injection attempts.
- English examples.
- Arabic examples.

The evaluation should check:

- Correct severity classification.
- Valid structured output.
- Correct refusal to diagnose.
- Correct escalation behavior.
- Relevant retrieved evidence.
- Safe handling of uncertainty.
- Natural multilingual output.

## Recommended Tech Stack

For a Data Science technical assessment, a suitable stack would be:

- Python
- Streamlit
- Pydantic for schema validation
- Local JSON or Markdown knowledge base
- TF-IDF, sentence embeddings, or another simple retrieval method
- OpenRouter, Ollama, or another free/low-cost model option
- A simple eval script or pytest-based evals

Streamlit is a good fit because it is easy to run, easy to demo, and natural for AI/Data Science prototypes.

## Deliverables

The final submission should include:

- Runnable GitHub repository.
- Streamlit app or equivalent UI.
- Curated pediatric safety knowledge base.
- RAG pipeline.
- Structured output schema.
- Safety guardrail logic.
- Evaluation script and test cases.
- README with setup, architecture, eval results, tradeoffs, and tooling transparency.
- 3-minute Loom video showing 5 inputs end-to-end.

The Loom should include at least one case where the system refuses, says it does not know, or escalates to medical care.

## Positioning Statement

This should be presented as:

> A bilingual pediatric urgency routing assistant for parents, grounded in curated safety guidance, with strict structured outputs and hard guardrails against diagnosis.

It should not be presented as:

> A medical diagnosis system.

## Success Criteria

The project is successful if it:

- Runs in under 5 minutes from setup.
- Uses RAG in a clear and explainable way.
- Produces schema-valid structured output.
- Handles English and Arabic inputs.
- Demonstrates strong uncertainty handling.
- Escalates risky symptoms safely.
- Includes honest evals with failures documented if any.
- Clearly explains architecture, tradeoffs, and tooling provenance.
