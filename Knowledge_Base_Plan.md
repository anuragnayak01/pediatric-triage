# Knowledge Base Plan

## Purpose

The knowledge base is the source of truth for the pediatric symptom triage assistant. It should support Retrieval-Augmented Generation, safety guardrails, citations, and explainability.

The system must not rely on random model memory for medical guidance. Every medical claim shown to the parent should be grounded in retrieved source material or handled through a documented safety rule.

## Current Source Inventory

### Clinical Guidelines

Located in:

```text
data/raw/clinical_guidelines/
```

Files:

- `WHO_ETAT_2005.pdf`
- `WHO_Pediatric_ETAT_2016.pdf`
- `ESI_v4_Handbook.pdf`

Use for:

- Emergency red flags.
- Pediatric emergency triage.
- Priority signs.
- Severity framework.
- Safety override logic.

### Parent Guidance

Located in:

```text
data/raw/parent_guidance/
```

Files:

- `AAP_Fever_When_To_Call.pdf`
- `Mayo_Sick_Baby.pdf`
- `Mayo_Fever_Children.pdf`
- `Mayo_Vomiting_Children.pdf`

Use for:

- Parent-facing fever guidance.
- Sick baby warning signs.
- Vomiting and dehydration escalation.
- Clear parent instructions.
- Natural, understandable safety wording.

## Runtime RAG Sources

The runtime RAG index should include:

- WHO ETAT sources.
- ESI v4 selected severity-framework sections.
- AAP fever guidance.
- Mayo sick baby guidance.
- Mayo fever guidance.
- Mayo vomiting guidance.

The runtime RAG index should not include:

- Research papers.
- General dialogue datasets.
- Broad biomedical QA datasets.
- Unverified web content.

## Source Roles

### WHO ETAT

Primary role:

- Pediatric emergency signs.
- Priority signs.
- Critical illness recognition.

Expected chunk topics:

- Airway and breathing.
- Shock.
- Coma or altered consciousness.
- Convulsions.
- Severe dehydration.
- Priority signs.

### WHO Pediatric ETAT 2016

Primary role:

- Updated pediatric emergency triage guidance.
- Evidence-backed emergency and priority treatment recommendations.

Expected chunk topics:

- Emergency signs.
- Priority signs.
- Triage decision logic.
- Severe dehydration.
- Respiratory distress.

### ESI v4 Handbook

Primary role:

- Acuity framework.
- Emergency department severity reasoning.

Use carefully:

- Do not expose ESI levels directly to parents.
- Use selected chunks only for internal severity mapping.

Expected chunk topics:

- Immediate life-saving intervention.
- High-risk situation.
- Altered mental status.
- Severe pain or distress.
- Resource/acuity framing.

### AAP / HealthyChildren Fever Guidance

Primary role:

- Parent-facing pediatric fever escalation.

Expected chunk topics:

- Fever in babies younger than 3 months.
- Fever duration.
- Fever plus red flags.
- When to call the pediatrician.

### Mayo Sick Baby

Primary role:

- Parent-facing infant warning signs.

Expected chunk topics:

- Feeding problems.
- Trouble breathing.
- Hard to wake.
- Dehydration.
- Temperature concerns.
- Persistent vomiting.

### Mayo Fever Children

Primary role:

- Parent-facing fever red flags.

Expected chunk topics:

- Fever with stiff neck.
- Fever with rash.
- Fever with breathing difficulty.
- Fever with dehydration.
- Fever duration.

### Mayo Vomiting Children

Primary role:

- Parent-facing vomiting and dehydration escalation.

Expected chunk topics:

- Vomiting blood.
- Green vomit.
- Severe abdominal pain.
- Dehydration.
- Inability to keep liquids down.

## Processing Flow

The knowledge base should be prepared through this pipeline:

```text
Raw PDFs
→ PDF text extraction with page numbers
→ text cleaning
→ section-aware chunking
→ metadata enrichment
→ saved chunks.jsonl
→ vector index creation
→ retrieval quality checks
```

## Folder Outputs

Raw sources:

```text
data/raw/
```

Processed chunks:

```text
data/processed/chunks.jsonl
```

Vector index:

```text
data/indexes/
```

Retrieval test results:

```text
data/processed/retrieval_checks.json
```

## Chunking Strategy

Use structural-first chunking with recursive fallback.

Chunks should be based on document meaning and medical context, not arbitrary page length. The default strategy is to preserve the source structure first, then recursively split only when a structural section is too large.

Recommended hierarchy:

```text
PDF
→ chapter or major heading
→ section or subsection
→ table or bullet block
→ paragraph group
→ recursive split only if oversized
```

Recommended chunk size:

- Target size: 350-500 words.
- Maximum size: around 700 words.
- Recursive split overlap: 60-100 words.
- Red-flag chunks may be smaller, around 150-300 words.

Chunk boundaries should prefer:

- Chapter headings.
- Section headings.
- Subsection headings.
- Bullet lists.
- Tables converted to readable text.
- Single clinical scenario.
- Single parent-facing guidance topic.

If a structural section is within the size limit, keep it whole. If it is oversized, split recursively by:

1. Subsection.
2. Bullet list.
3. Paragraph.
4. Sentence.

Avoid chunks that combine unrelated topics, such as fever rules and trauma rules in one chunk.

The final rule:

> Structural chunking is the default. Recursive chunking is a fallback for oversized structural sections only.

## Chunk Metadata Schema

Each chunk should include:

- `chunk_id`
- `source_file`
- `source_name`
- `source_type`
- `source_url`
- `page_start`
- `page_end`
- `section_title`
- `chapter_title`
- `subsection_title`
- `topic`
- `severity_relevance`
- `age_group`
- `language`
- `keywords`
- `chunking_method`
- `parent_section_id`
- `split_index`
- `text`

Recommended values for `source_type`:

- `clinical_guideline`
- `parent_guidance`
- `triage_framework`

Recommended values for `severity_relevance`:

- `mild`
- `monitor`
- `see-doctor`
- `emergency`
- `mixed`
- `unknown`

Recommended values for `age_group`:

- `infant_under_3_months`
- `infant_3_to_12_months`
- `child_under_2_years`
- `child_2_years_plus`
- `all_children`
- `unknown`

Recommended values for `chunking_method`:

- `structural`
- `recursive_from_structural`

## Cleaning Rules

Remove:

- Repeated headers and footers.
- Page numbers when they are not useful.
- Navigation text.
- Copyright boilerplate if repeated on every page.
- Broken hyphenation.
- Duplicate chunks.

Preserve:

- Page numbers.
- Section headings.
- Tables with clinical rules.
- Bullet lists.
- Source attribution.
- Exact medical thresholds such as `100.4°F / 38°C`.

## Retrieval Strategy

Recommended approach:

1. Use metadata-aware retrieval.
2. Use semantic retrieval for symptoms.
3. Use keyword or hybrid retrieval for exact red flags and thresholds.
4. Prefer parent-guidance chunks for parent-facing wording.
5. Prefer clinical-guideline chunks for safety overrides.

Best retrieval behavior:

- Retrieve top 4-6 chunks.
- Require at least one relevant chunk for medical reasoning.
- If no chunk passes relevance threshold, return uncertainty.
- Include retrieved chunk IDs in structured output.

## Citation Strategy

Every medical recommendation should cite retrieved evidence.

The UI should show:

- Source name.
- Page number where available.
- Section title where available.
- Short retrieved excerpt.

The parent-facing answer should be concise, but the evaluator-facing "Why this assessment?" panel should show the evidence.

## Safety Rule Extraction

Some rules should be extracted from the knowledge base into deterministic safety checks.

Hard override candidates:

- Child under 3 months with fever >= 100.4°F / 38°C.
- Breathing difficulty.
- Blue lips, tongue, or nails.
- Stopped breathing.
- Seizure.
- Unresponsive or cannot be awakened.
- Severe dehydration with lethargy.
- Poisoning.
- Heavy bleeding.
- Severe burns.
- Vomiting blood.
- Green vomit.
- Stiff neck with fever.

These rules should not depend only on the LLM.

## Retrieval Quality Checks

Before building the triage model, run retrieval checks.

Test queries should include:

1. `2 month old baby fever 101`
2. `child has blue lips and trouble breathing`
3. `seizure and not waking up`
4. `no wet diaper for 10 hours`
5. `vomiting green liquid`
6. `fever for 4 days`
7. `mild cough and runny nose playing normally`
8. `rash with fever and stiff neck`
9. `child swallowed poison`
10. `Arabic query for fever and dehydration`

Each retrieval check should record:

- Query.
- Top retrieved chunk IDs.
- Source names.
- Whether expected topic was retrieved.
- Whether retrieved evidence is sufficient.

## Quality Bar

The knowledge base is ready only when:

- Every chunk has source metadata.
- Emergency topics are easy to retrieve.
- Fever age rules are easy to retrieve.
- Dehydration topics are easy to retrieve.
- Parent guidance is distinguishable from clinical guideline content.
- Retrieval failures are documented.
- Weak retrieval triggers uncertainty instead of hallucination.

## Initial Success Criteria

Before moving to model generation, confirm:

- `chunks.jsonl` exists.
- At least 40-80 high-quality chunks are produced.
- Each source contributes useful chunks.
- Retrieval checks pass for core emergency and fever cases.
- Safety override rules have clear source support.

 
