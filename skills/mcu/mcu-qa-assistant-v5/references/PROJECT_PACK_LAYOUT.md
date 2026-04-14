# Project Pack Layout

Use this file before reading any project knowledge pack.

## Layout Detection Order

**Always check Layout C first**, then Layout B, then Layout A:

1. **Layout C?** Directory contains `00_阅读指南.md` + at least 5 `0X_*.md` files + no `06_knowledge/` or `machine_index/` → **Layout C**
2. **Layout B?** Directory contains `06_knowledge/machine_index/` with `concept_index.jsonl` → **Layout B**
3. **Layout A?** Directory contains `03_structured_kb/` → **Layout A**

## Supported Layouts

### Layout C: V10 Flat MD Pack

Produced by `mcu-project-organizer-v10`. Valid user entry point: the project knowledge base root directory.

```text
<project_kb_root>/
├── 00_阅读指南.md
├── 01_项目介绍.md
├── 02_硬件配置.md
├── 03_系统架构.md
├── 04_功能模块.md
├── 05_通信协议.md
├── 06_关键参数表.md
├── 07_已知问题与建议.md
├── _utf8_temp/          # optional
└── _v10_context/        # optional
```

No `machine_index/`, no `08_ai_enrichment/`, no `09_source_snapshot/`.

### Layout B: Current pack layout shared by V4/V6/current V8/V9

Valid user entry points:

- pack root that contains `06_knowledge/`
- `.../06_knowledge/`
- `.../06_knowledge/machine_index/`

Typical pack root:

```text
<run_root>/
├── 06_knowledge/
│   ├── human_docs/
│   └── machine_index/
├── 08_ai_enrichment/
└── 09_source_snapshot/
```

Common high-value AI artifacts inside `08_ai_enrichment/` include:

- `concept_inventory.json`
- `concept_relations.json`
- `debug_playbook.json`
- `verification_playbook.json`
- `core_concept_type_templates.md`
- `critical_detail_facts.json`
- `qa_code_analysis_playbook.json`

## Required Read Order

### Layout C (V10 Flat MD)

1. Classify the question type (see `V10_FLAT_MD_ADDENDUM.md` routing table).
2. Read the **primary** V10 document for that question type.
3. If partial, read the **secondary** document.
4. If still insufficient, scan remaining V10 documents.
5. Fall back to public knowledge base or web search.

### Layout B (V4/V6/V8/V9)

1. `machine_index/kb_manifest.json`
2. `machine_index/doc_catalog.json`
3. `machine_index/question_patterns.json`
4. `machine_index/fact_index.jsonl`
5. `machine_index/search_index.jsonl`
6. `machine_index/concept_index.jsonl`
7. `machine_index/relation_index.jsonl`
8. `machine_index/inference_index.jsonl` if needed
9. `machine_index/advice_index.jsonl` if needed
10. `machine_index/entity_index.json` if needed
11. `machine_index/evidence_refs.jsonl` if needed
12. concept artifact docs referenced by `doc_catalog.json`, especially:
    - `08_ai_enrichment/critical_detail_facts.json`
    - `08_ai_enrichment/qa_code_analysis_playbook.json`
    - `08_ai_enrichment/concept_inventory.json`
    - `08_ai_enrichment/concept_relations.json`
    - `08_ai_enrichment/debug_playbook.json`
    - `08_ai_enrichment/verification_playbook.json`
    - `08_ai_enrichment/core_concept_type_templates.md`
13. relevant `human_docs/*.md`
14. `09_source_snapshot/` last

## Detail-First Rule

For exact-value questions such as timebase, timeout, retry count, threshold, period, frequency, or default value:

**Layout C**: Open `06_关键参数表.md` first. If found with source reference, treat as verified. If not, check `02_硬件配置.md`.

**Layout B**:
1. Check `critical_detail_facts.json` first when available.
2. Use resolved detail items before long prose.
3. If the detail item is not resolved, fall through to governed fallback.
4. Do not answer from the first similar number found in `human_docs`.

## Fallback Rule

**Layout C**: There is no source snapshot fallback. If V10 documents are insufficient, state the gap explicitly and suggest the user provide source files.

**Layout B**: When `09_source_snapshot` exists:
- use `qa_code_analysis_playbook.json` before opening arbitrary source files
- keep source analysis constrained to the minimum target-scoped files needed

## Forbidden Behavior

- do not fail or refuse when `machine_index/` is missing (it is expected for Layout C)
- do not scan the whole raw repo before checking `machine_index` (Layout B)
- do not ignore `critical_detail_facts.json` for exact-detail questions (Layout B)
- do not ignore `question_patterns.json` and `concept_index.jsonl` for concept-first questions (Layout B)
- do not jump straight into long human docs (Layout B)
- do not perform free-form source analysis when a governed playbook route exists (Layout B)
