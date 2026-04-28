# Technical Assessment Guidelines

These guidelines were extracted from the provided NotebookLM source for the Mumzworld technical assessment. Use this file as the working checklist before choosing, building, evaluating, and submitting the project.

## Core Objective

- Build a prototype for a real Mumzworld use case.
- The use case may be customer-facing, internal tooling, or operations-focused.
- Prefer a novel, well-defended problem over a generic implementation of an obvious example.
- The project should demonstrate judgment in problem selection, not just coding ability.

## Required AI Engineering Depth

The project must include at least two non-trivial AI engineering elements, such as:

- Agent design or tool use.
- Multimodal input.
- Retrieval-augmented generation.
- Structured output with schema validation.
- Rigorous evaluations.
- Fine-tuning.
- Retrieval over messy data.

Do not submit a simple wrapper around a single prompt. The prototype should combine real engineering pieces such as data handling, APIs, a small UI, evaluations, and AI integration.

## Multilingual Requirement

- The solution must work in both English and Arabic.
- Arabic output must read naturally and natively.
- Literal machine-translated Arabic will be penalized.

## Grounding and Uncertainty

- The system must not invent unsupported facts.
- If information is missing or unsupported, the system must explicitly return `"I don't know"` or `null`.
- The system must not pad answers with generic claims.
- The system must not answer confidently when the input is out of scope.
- Refusal and uncertainty behavior should be visible in both implementation and evaluation.

## Structured Output

- All structured outputs must validate against a defined schema.
- Malformed JSON is penalized.
- Do not cheat validation with empty strings.
- Include explicit failure handling for invalid or unsupported outputs.

## Data and Tooling Constraints

- The project is scoped for roughly 5 hours.
- If more time is spent, document where the extra time went.
- Bring or generate your own data.
- Do not scrape retailer sites.
- Paid API keys are not required.
- Free or AI-assisted tools are allowed and encouraged.
- Heavy AI assistance is allowed, but provenance must be documented honestly.

## Suggested Project Examples

Customer-facing examples:

- Voice memo to structured shopping list or calendar items.
- Product image to launch-ready product detail page content.
- Review summarizer that turns many reviews into a "Moms Verdict."
- Pregnancy due date to week-by-week content and product timeline.
- Pediatric symptom triage that clearly defers to doctors.
- Gift finder with reasoning, such as "under 200 AED."
- Blog post generator comparing 2-5 products with tables, pros and cons, and citations.

Internal tooling examples:

- Free-text return reason classifier with category, reasoning, and confidence score.
- Customer service email triage with intent, urgency, and suggested reply.
- Embedding-based duplicate catalog detector with reviewable diff and confidence score.

Operations examples:

- Dashboard over order data by day, country, and category with anomaly detection and AI-written weekly summary.

## Recommended Project Selection Criteria

Prefer a project that can demonstrate:

- A real Mumzworld business or customer problem.
- Bilingual English and Arabic behavior.
- Schema-validated structured output.
- Clear uncertainty handling.
- At least 10 meaningful eval cases.
- A small but usable UI.
- A setup path that works in under 5 minutes.

Strong finishable options include:

- Return reason classifier.
- Customer service email triage.
- Review summarizer.
- Gift finder.

## Deliverables

The final submission must include:

- A clean GitHub repository.
- Runnable code that can be cloned, set up, and run to first output in under 5 minutes.
- A 3-minute Loom video.
- A comprehensive README.

The Loom video must show:

- 5 inputs running end-to-end.
- At least one example where the model refuses, returns uncertainty, or says it does not know.

## README Requirements

The README should include clearly separated sections for:

- Setup instructions.
- Evaluation rubric.
- At least 10 test cases.
- A mix of easy and adversarial inputs.
- Honest scores and failures.
- Tradeoffs and rejected ideas.
- Architecture and model choices.
- How uncertainty was handled.
- What was cut for time.
- Future improvements.
- Tooling transparency.

The tooling transparency section should include:

- Exact tools and models used.
- Specific pairings, such as model plus provider or harness.
- How AI tools were used.
- What worked.
- What failed.
- Any places where manual intervention overruled AI output.
- Material prompts, system messages, or configuration that shaped the final output.

Prompts and configurations should either be pasted into the README or committed elsewhere in the repository.

## Code Quality Expectations

- Keep the repository clean and easy to inspect.
- Include clear inline comments where code is non-obvious.
- Avoid unnecessary abstractions.
- Make setup predictable.
- Keep the evaluator's first-run path simple.
- Ensure outputs are production-quality enough for a prototype.

## Evaluation Criteria

The assessment is weighted as follows:

- 30% Execution: Does the code run, and is the output production-quality?
- 25% Eval rigor: Did the project prove the prototype works?
- 20% Problem selection: Is the problem real and high-leverage?
- 15% Uncertainty handling: Does the system know what it does not know?
- 10% Code clarity and tooling transparency: Is the repo clean and honestly documented?

## Common Pitfalls

- Scraping retailer sites.
- Hiding AI provenance.
- Returning malformed JSON.
- Using empty strings to pass schema validation.
- Making unsupported claims.
- Giving confident answers to out-of-scope inputs.
- Producing Arabic that reads like literal translation.
- Shipping a prompt-only demo with no meaningful engineering.
- Omitting adversarial evals.
- Failing to show uncertainty handling in the Loom.

## Working Checklist

Before building:

- Pick a real Mumzworld problem.
- Confirm the project includes at least two non-trivial AI engineering elements.
- Define the schema for structured output.
- Define unsupported and out-of-scope behavior.
- Prepare or generate data without scraping retailer sites.

During building:

- Implement bilingual English and Arabic handling.
- Validate structured outputs.
- Add explicit failure handling.
- Keep setup simple.
- Track AI tools and prompts used.

Before submission:

- Run at least 10 eval cases.
- Include easy and adversarial tests.
- Report failures honestly.
- Confirm the app runs from setup to first output in under 5 minutes.
- Record a 3-minute Loom with 5 inputs and one uncertainty/refusal case.
- Complete README sections for setup, evals, tradeoffs, tooling, and future work.
