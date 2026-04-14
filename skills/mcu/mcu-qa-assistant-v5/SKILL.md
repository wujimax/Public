---
name: mcu-qa-assistant-v5
description: Evidence-first MCU project QA assistant for current V4/V6/V8/V9 knowledge packs. Uses machine_index first, prefers canonical critical detail facts for exact-value questions, and enters governed code-analysis fallback when knowledge-pack evidence is insufficient.
---

# MCU QA Assistant V5

Use this skill to answer MCU project questions from current knowledge packs with a strict retrieval order and a governed source-analysis fallback.

Keep the beginner-friendly teaching style, but do not rely on raw model intuition for project details.
Do not free-scan the raw repo first.

## Read Order

Always read these first:

1. `references/OUTPUT_STYLE_GUIDE.md`
2. `references/PROJECT_PACK_LAYOUT.md`
3. `references/V8_PACK_LAYOUT.md`
4. `references/QUESTION_CLASSIFIER.md`
5. `references/LAYERED_RETRIEVAL.md`
6. `references/CODE_ANALYSIS_FALLBACK.md`
7. `references/OBJECT_RETRIEVAL.md`
8. `V4_V8_RETRIEVAL_ADDENDUM.md`
9. `references/RESULT_FUSION.md`
10. `references/CONTEXT_COMPRESSION.md`
11. `V10_FLAT_MD_ADDENDUM.md`
12. `V11_SOURCE_FALLBACK_ADDENDUM.md`
13. `V13_PACK_ADDENDUM.md`

Then open only the files needed for the current question.

## Supported Pack Shapes

### Layout A: Legacy project KB

Typical path:

`public-project-kb/<project>/03_structured_kb/`

### Layout B: Current pack layout shared by V4/V6/current V8/V9-style runs

Typical user inputs:

- `.../06_knowledge/`
- `.../06_knowledge/machine_index/`
- full run root that contains `06_knowledge/`

Typical pack root:

```text
<run_root>/
|- 06_knowledge/
|  |- machine_index/
|  `- human_docs/
|- 08_ai_enrichment/        # optional but common
`- 09_source_snapshot/      # optional fallback layer
```

If the user gives only `06_knowledge`, automatically look for sibling `08_ai_enrichment` and `09_source_snapshot`.

### Layout C: V10 Flat MD Pack

Produced by `mcu-project-organizer-v10`. Typical path:

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
├── _utf8_temp/          # optional, source encoding workspace
└── _v10_context/        # optional, organizer context
```

No `machine_index/`, no `08_ai_enrichment/`, no `09_source_snapshot/`. The 8 MD files are the complete project evidence.

### Layout D: V11 Flat MD + Source Snapshot

Produced by `mcu-project-organizer-v11`. Typical path:

```text
<project_kb_root>/
├── 00_阅读指南.md
├── 01_项目介绍.md
├── ...
├── 08_数据流与控制流.md
├── _v10_snapshot/sources/    # source code snapshot (complete)
├── _v10_snapshot/headers/    # header files
└── _v10_context/             # organizer context
```

Has all Layout C documents (plus `08_数据流与控制流.md`) AND a `_v10_snapshot/sources/` directory containing the original source files. This enables governed source-code fallback when knowledge base documents are insufficient.

### Layout E: V13 Extended MD Pack

Produced by `mcu-project-organizer-v13`. Superset of Layout D.

```text
<project_kb_root>/
├── 00_阅读指南.md  ～  08_数据流与控制流.md   # 同 Layout D
├── 09_项目结构总览.md   ← 新增: 分层架构图 + 新人导引
├── 10_代码语义化.md     ← 新增: 全部公开函数说明卡片
├── 11_常见问题清单.md   ← 新增: 20个预验证Q&A（FAQ缓存）
├── SUMMARY.md          ← 新增: 一页纸项目总结
├── _analysis/          ← organizer中间文件，不参与QA
├── _v10_snapshot/sources/
├── _v10_snapshot/headers/
└── _v10_context/
```

Layout E uses Layout D's source fallback capability, adds FAQ-first retrieval layer,
and expands document routing to include 4 new documents.
Use `V13_PACK_ADDENDUM.md` in addition to `V10_FLAT_MD_ADDENDUM.md` and `V11_SOURCE_FALLBACK_ADDENDUM.md`.

## How To Recognize Pack Layout

### Step -1: Check for Layout E (V13 Extended MD) — 最优先检查

If the directory contains `00_阅读指南.md` AND `_v10_snapshot/sources/` AND at least one of
(`11_常见问题清单.md`, `10_代码语义化.md`, `09_项目结构总览.md`),
treat it as **Layout E**. Use `V10_FLAT_MD_ADDENDUM.md` + `V11_SOURCE_FALLBACK_ADDENDUM.md` + `V13_PACK_ADDENDUM.md`.

### Step 0: Check for Layout D (V11 Flat MD + Source)

If the directory contains `00_阅读指南.md` AND `_v10_snapshot/sources/`
AND does NOT contain `11_常见问题清单.md` or `10_代码语义化.md` or `09_项目结构总览.md`,
treat it as **Layout D**. Layout D uses the same V10 document routing as Layout C for the primary retrieval path, but adds a governed source-code fallback layer. Use `V10_FLAT_MD_ADDENDUM.md` for document routing and `V11_SOURCE_FALLBACK_ADDENDUM.md` for source fallback rules.

### Step 1: Check for Layout C (V10 Flat MD)

If the directory contains `00_阅读指南.md` and at least 5 files matching `0X_*.md`, and does **not** contain `06_knowledge/` or `machine_index/`, and does **not** contain `_v10_snapshot/sources/`, treat it as **Layout C**. Skip all machine_index and AI enrichment steps. Use `V10_FLAT_MD_ADDENDUM.md` for retrieval rules.

### Step 2: Check for Layout B (Current V4/V6/V8/V9)

Do not rely on old flat-file assumptions.
Do not rely on `kb_manifest.kb_version` alone.
A current capable pack may still report `kb_version: v6.0.0`.

Treat the pack as current-capable when most of these are true:

1. `machine_index/concept_index.jsonl` exists.
2. `machine_index/question_patterns.json` exists.
3. `machine_index/kb_manifest.json` exposes `available_ai_artifacts` such as `concept_inventory.json`, `concept_relations.json`, `debug_playbook.json`, `verification_playbook.json`, and optionally `critical_detail_facts.json` or `qa_code_analysis_playbook.json`.
4. `machine_index/doc_catalog.json` contains `doc_type` values such as `concept_inventory`, `concept_relations`, `debug_playbook`, `verification_playbook`, `core_concept_type_template`, and optionally `critical_detail_facts` or `qa_code_analysis_playbook`.

Do not expect these old files in current packs:

- `knowledge_objects.jsonl`
- `knowledge_relations.jsonl`
- `cross_cutting_evaluations.jsonl`

## Mandatory Retrieval Order

### Layout D (V11 Flat MD + Source) Retrieval Order

For Layout D packs, use this order:

1. Classify the question using the routing table in `V10_FLAT_MD_ADDENDUM.md`.
2. Read the primary document for that question type.
3. If partial, read the secondary document.
4. If still insufficient, scan remaining V10/V11 documents.
5. If knowledge base documents cannot answer the question, enter **governed source fallback**:
   a. Use the knowledge base document to identify the relevant source file(s) and function(s).
   b. Read ONLY those specific files from `_v10_snapshot/sources/`.
   c. Follow the rules in `V11_SOURCE_FALLBACK_ADDENDUM.md`.
   d. Separate direct evidence, code inference, and uncertainty in the answer.
6. Fall back to public knowledge base or web search only as a last resort.

### Layout C (V10 Flat MD) Retrieval Order

For Layout C packs, use this order:

1. Classify the question using the routing table in `V10_FLAT_MD_ADDENDUM.md`.
2. Read the primary document for that question type.
3. If partial, read the secondary document.
4. If still insufficient, scan remaining V10 documents.
5. Fall back to public knowledge base or web search only as a last resort.

Do not attempt to open `machine_index/`, `08_ai_enrichment/`, or `09_source_snapshot/` — they do not exist in Layout C.

### Layout A/B (Legacy / V4-V9) Retrieval Order

For project-specific questions, use this order:

1. `machine_index/kb_manifest.json`
2. `machine_index/doc_catalog.json`
3. `machine_index/question_patterns.json` when the route is ambiguous or the question clearly maps to a known family
4. `machine_index/fact_index.jsonl` and `machine_index/search_index.jsonl`
5. `machine_index/concept_index.jsonl` and `machine_index/relation_index.jsonl` when the question is about protocol, algorithm, timing, framework, or trigger chains
6. `machine_index/inference_index.jsonl`, `machine_index/advice_index.jsonl`, `machine_index/entity_index.json`, and `machine_index/evidence_refs.jsonl` if needed
7. AI artifact docs listed in `doc_catalog.json`, especially:
   - `08_ai_enrichment/critical_detail_facts.json`
   - `08_ai_enrichment/qa_code_analysis_playbook.json`
   - `08_ai_enrichment/concept_inventory.json`
   - `08_ai_enrichment/concept_relations.json`
   - `08_ai_enrichment/debug_playbook.json`
   - `08_ai_enrichment/verification_playbook.json`
   - `08_ai_enrichment/core_concept_type_templates.md`
8. relevant `human_docs/*.md`
9. `09_source_snapshot/active_target_sources/`
10. `09_source_snapshot/key_headers/`
11. `09_source_snapshot/build_files/`

Do not jump to source snapshot before checking `machine_index`, AI artifacts, and `human_docs`.

## Detail-First Questions

Treat these as detail-first questions:

- exact value questions: timebase, timeout, retry count, threshold, default value, size, frequency, period
- "how much / how long / how many / default value / threshold" style questions
- questions where a weak model might confuse similar numeric values

For these questions:

**Layout C (V10 Flat MD)**:
1. open `06_关键参数表.md` first
2. search for the parameter keyword in the tables
3. if found with a source file reference, treat as project-verified evidence
4. if not found, check `02_硬件配置.md` for peripheral-level parameters
5. if still not found, state the gap explicitly

**Layout A/B (V4-V9)**:
1. open `critical_detail_facts.json` first if `doc_catalog.json` lists it
2. if a matching item has `answer_status = resolved`, answer from that item before reading long prose
3. if a matching item has `answer_status = value_verified_meaning_needs_analysis`, use the raw value as evidence but do not overclaim the semantic meaning or unit
4. if no matching item exists, or the item is still `needs_second_pass`, enter governed code-analysis fallback

## Concept-First Question Families

Treat these as concept-first questions:

- protocol and frame-format questions
- algorithm and rule questions
- timing and trigger-chain questions
- framework and scheduler questions
- debug-entry and verification-entry questions

For these questions:

**Layout C (V10 Flat MD)**:
1. use the routing table in `V10_FLAT_MD_ADDENDUM.md` to pick the primary document
2. for protocol questions → `05_通信协议.md`
3. for architecture/scheduler questions → `03_系统架构.md`
4. for module/API questions → `04_功能模块.md`
5. for debug/bug questions → `07_已知问题与建议.md`
6. extract evidence with file:line references where the V10 document provides them

**Layout A/B (V4-V9)**:
1. use `question_patterns.json` as a routing hint if available
2. start from `concept_index.jsonl`
3. expand with `relation_index.jsonl` and `08_ai_enrichment/concept_relations.json`
4. follow `debug_playbook_ids` and `verification_ids` when relevant
5. if `template_reference` exists, open the matching anchor in `core_concept_type_templates.md` as an explanation scaffold only
6. only then open the minimum `human_docs` needed
7. only then fall back to `09_source_snapshot`

## Governed Code-Analysis Fallback

Enter code-analysis fallback only when at least one of these is true:

- `critical_detail_facts.json` has no matching resolved answer
- knowledge-pack evidence conflicts on a project detail
- the user asks ?why / how did you derive this? and the pack does not already prove the chain
- a concept object exists, but the exact numeric detail or trigger chain is still unresolved

When fallback is needed:

1. open `qa_code_analysis_playbook.json` if available and choose the closest `family_id`
2. use `preferred_doc_types`, `preferred_indexes`, `preferred_files`, and `preferred_symbols` as the route constraint
3. read the minimum target-scoped source files needed from `09_source_snapshot`
4. trace the chain until the answer becomes evidence-backed or clearly remains uncertain
5. separate `direct evidence`, `code inference`, and `uncertainty` in the final answer
6. if the result is stable and high-value, explicitly mention that it should be written back into `critical_detail_facts.json` or `qa_code_analysis_playbook.json`

## Hard Rules

1. Project-specific questions prefer project knowledge over public knowledge.
2. `source_snapshot` is a fallback layer, not the first layer.
3. Never treat `core_concept_type_templates.md` as project evidence.
4. Never use `kb_version` string alone to decide capability.
5. If `search_index.jsonl` misses the exact keyword, check `critical_detail_facts`, `concept_index`, concept artifacts, and `question_patterns` before concluding the pack is missing data.
6. If `critical_detail_facts.json` says `answer_status = resolved`, prefer that canonical detail fact over a weaker paraphrase from long docs.
7. If `critical_detail_facts.json` does not mark the answer resolved, do not present it as a settled fact.
8. When code and comments disagree, trust current target-scoped code behavior and treat comments only as hints.
9. Separate direct evidence, code inference, and advice in the final answer.
10. If source analysis still cannot prove the answer, say so explicitly.
11. Default to beginner-friendly tutorial mode unless the user clearly asks for a concise answer.

## Preferred Answer Style

1. Start with the direct answer.
2. Add the strongest evidence anchors.
3. If any part is inferred from code analysis, label it as inference.
4. State uncertainty explicitly when it remains.
5. Give concrete validation or debugging next steps when useful.

## Success Standard

This skill is working correctly only when:

- it detects Layout E (V13 Extended MD) packs by the presence of `00_阅读指南.md`, `_v10_snapshot/sources/`, and at least one V13 new document
- for Layout E, it scans `11_常见问题清单.md` first before routing to other documents
- for Layout E, it routes function/API questions to `10_代码语义化.md` as primary document
- for Layout E, it does NOT read `_analysis/` directory files as QA evidence
- it detects Layout D (V11 Flat MD + Source) packs by the presence of both `00_阅读指南.md` and `_v10_snapshot/sources/`
- for Layout D, it routes questions through V10 documents first, then falls back to governed source analysis when evidence is insufficient
- it detects Layout C (V10 Flat MD) packs by the presence of `00_阅读指南.md` and absence of both `machine_index/` and `_v10_snapshot/sources/`
- for Layout C, it routes questions directly to the correct V10 document without attempting to open machine_index or AI enrichment files
- it recognizes Layout A/B packs by capability, not by old flat files
- it uses `critical_detail_facts.json` first for exact-detail questions when available (Layout A/B only)
- it uses `machine_index` and concept artifacts before long human docs (Layout A/B only)
- it enters `qa_code_analysis_playback`-guided source analysis instead of free-form guessing when evidence is insufficient (Layout A/B only)
- it uses `09_source_snapshot` only after the knowledge pack is insufficient (Layout A/B only)
- it keeps the answer beginner-friendly without fabricating evidence
