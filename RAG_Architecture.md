# RAG Architecture

## Purpose

This document defines the Retrieval-Augmented Generation architecture for the pediatric symptom triage project.

The RAG system must be source-grounded, explainable, and safe. It should retrieve relevant pediatric guidance from trusted PDFs, preserve citations, and support structured triage output. It should not rely on model memory for medical claims.

## Design Principle

Use proper libraries for production-quality implementation.

The system should avoid scratch-built PDF parsing, embedding, vector search, and schema validation when reliable libraries are available.

## Recommended Stack

### PDF Parsing

Recommended library:

- `PyMuPDF`

Purpose:

- Extract text from PDFs.
- Preserve page numbers.
- Support document-level and page-level metadata.

Why:

- Lightweight.
- Reliable for PDFs.
- Easier to control than generic document loaders.

### Chunking

Recommended approach:

- Structural-first chunking.
- Recursive fallback for oversized structural sections.

Possible libraries:

- `llama-index` node parsers.
- `langchain-text-splitters` for recursive fallback.

Policy:

- Structural chunking is the default.
- Recursive splitting is used only when a structural section is too large.

### Embeddings

Recommended library:

- `sentence-transformers`

Recommended model options:

- `BAAI/bge-m3`
- `intfloat/multilingual-e5-base`
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Recommended default:

- `intfloat/multilingual-e5-base`

Why:

- Supports multilingual retrieval.
- Better fit for English and Arabic than English-only embeddings.
- Avoids needing separate Arabic translation for every retrieval query.

### Vector Database

Recommended library:

- `ChromaDB`

Index location:

```text
data/indexes/chroma/
```

Why:

- Easy local persistence.
- Works well with Streamlit prototypes.
- Simple enough for evaluators to run.

### Reranking

Recommended:

- Optional cross-encoder reranking.

Possible model:

- `cross-encoder/ms-marco-MiniLM-L-6-v2`

Use if time allows.

Fallback:

- Use Chroma top-k retrieval with metadata filtering and relevance threshold.

### Structured Output Validation

Recommended library:

- `Pydantic`

Purpose:

- Enforce strict output schema.
- Prevent malformed JSON.
- Reject empty strings.
- Trigger safe fallback on validation failure.

### UI

Recommended library:

- `Streamlit`

Purpose:

- Data Science friendly interface.
- Fast demo.
- Shows RAG evidence, structured JSON, and eval examples clearly.

## Source Folders

Raw PDFs:

```text
data/raw/clinical_guidelines/
data/raw/parent_guidance/
```

Processed chunks:

```text
data/processed/chunks.jsonl
```

Vector index:

```text
data/indexes/chroma/
```

Retrieval checks:

```text
data/processed/retrieval_checks.json
```

## End-to-End RAG Flow

```text
Raw PDFs
→ PyMuPDF text extraction with page numbers
→ text cleaning
→ structural-first chunking
→ recursive fallback for oversized sections
→ metadata enrichment
→ save chunks.jsonl
→ create embeddings
→ persist ChromaDB index
→ retrieve top-k chunks for parent query
→ rerank or threshold-filter chunks
→ pass trusted evidence to model
→ validate structured output
→ apply hard safety overrides
→ return final response with citations
```

## Ingestion Flow

The ingestion pipeline should:

1. Load each PDF from `data/raw/`.
2. Extract text page by page.
3. Preserve source file and page number.
4. Clean extracted text.
5. Detect headings and sections where possible.
6. Create structural chunks.
7. Recursively split oversized chunks.
8. Add metadata.
9. Save chunks to `data/processed/chunks.jsonl`.
10. Build or refresh the ChromaDB index.

## Chunk Metadata

Each chunk should contain:

- `chunk_id`
- `source_file`
- `source_name`
- `source_type`
- `source_url`
- `page_start`
- `page_end`
- `chapter_title`
- `section_title`
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

## Retrieval Query Flow

For each parent input:

1. Detect input language.
2. Extract or infer key query terms:
   - age
   - temperature
   - symptoms
   - duration
   - breathing status
   - hydration status
   - alertness
3. Build retrieval query from original input plus extracted concepts.
4. Retrieve top-k chunks.
5. Apply metadata filters when useful.
6. Rerank if enabled.
7. Keep only chunks above relevance threshold.
8. If insufficient evidence remains, set uncertainty.

## Retrieval Settings

Recommended initial settings:

- `top_k`: 6
- `minimum_relevance_threshold`: tune after retrieval checks
- `max_context_chunks`: 4
- `prefer_parent_guidance`: true for parent-facing wording
- `prefer_clinical_guidelines`: true for safety override checks

## Hybrid Retrieval

Medical red flags often depend on exact terms, such as:

- blue lips
- seizure
- no wet diapers
- 100.4°F
- 38°C
- cannot be awakened

The system should support hybrid retrieval if possible:

- vector retrieval for semantic similarity
- keyword matching for exact red flags and thresholds

If full hybrid retrieval is not implemented, the safety layer should still keyword-match critical red flags before final output.

## Reranking Strategy

Reranking is optional but recommended if time allows.

Use reranking to:

- reduce irrelevant chunks
- improve source precision
- prioritize exact pediatric guidance
- avoid retrieval noise

If reranking is skipped, document it as a tradeoff and rely on:

- top-k retrieval
- metadata filtering
- safety overrides
- retrieval quality checks

## Citation Strategy

The final response should cite retrieved chunks.

Each displayed citation should include:

- source name
- source file
- page number
- section title if available
- short evidence excerpt

The UI should include a "Why this assessment?" section showing:

- matched rules
- retrieved chunks
- source citations
- safety rationale

## Weak Retrieval Behavior

If retrieval is weak, irrelevant, or empty, the system must not hallucinate.

Fallback behavior:

- Set `uncertainty_flag = true`.
- Use `need-more-info` or `monitor` depending on symptoms.
- Ask focused follow-up questions.
- Include emergency red flag warning.
- Avoid specific medical claims not supported by retrieved evidence.

## Safety Override Integration

RAG retrieval is not the final safety authority.

The final decision flow should be:

```text
model structured output
→ schema validation
→ hard safety override checks
→ final output
```

Hard safety overrides should come from documented pediatric red flags and age-specific fever rules.

Examples:

- Breathing difficulty: force `emergency`.
- Blue lips: force `emergency`.
- Seizure: force `emergency`.
- Unresponsive: force `emergency`.
- Baby under 3 months with fever >= 100.4°F / 38°C: force at least `see-doctor`.
- Weak retrieval: force uncertainty.

## Retrieval Quality Checks

Before model generation is considered reliable, test retrieval with known queries.

Required retrieval checks:

1. `2 month old baby fever 101`
2. `child has blue lips and trouble breathing`
3. `seizure and not waking up`
4. `no wet diaper for 10 hours`
5. `vomiting green liquid`
6. `fever for 4 days`
7. `mild cough and runny nose playing normally`
8. `rash with fever and stiff neck`
9. `child swallowed poison`
10. Arabic query for fever and dehydration.

Each check should record:

- query
- top chunk IDs
- source names
- retrieved topics
- pass/fail
- notes

## Evaluation Link

Retrieval quality should be part of the project evaluation.

The final evals should check:

- severity correctness
- structured output validity
- retrieved evidence relevance
- no unsupported medical claims
- correct uncertainty behavior
- correct safety override behavior
- Arabic input/output quality

## README Notes

The README should explain:

- why RAG was used
- why these sources were selected
- how PDF ingestion works
- how structural chunking works
- how retrieval quality was checked
- how weak retrieval triggers uncertainty
- why safety overrides exist beyond RAG

## Locked Decision

Use this architecture unless a strong implementation blocker appears:

```text
PyMuPDF
→ structural-first chunking
→ recursive fallback
→ sentence-transformers multilingual embeddings
→ ChromaDB
→ optional reranking
→ Pydantic validation
→ deterministic safety overrides
→ Streamlit UI
```
