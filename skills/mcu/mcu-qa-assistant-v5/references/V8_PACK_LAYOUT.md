# V8/V9 知识包布局（当前真实形态）

最后更新：2026-03-22
版本：V5

这份文档说明的是当前真实可用的 V8/V9 能力包，不是旧版扁平对象文件包。

## 一句话结论

当前能力包的外层结构仍然是：

- `06_knowledge/`
  - `machine_index/`
  - `human_docs/`
- sibling `08_ai_enrichment/`
- sibling `09_source_snapshot/`

增强点不在于外层换目录，而在于：

- `concept_index.jsonl`
- `question_patterns.json`
- `core_concept_type_templates.md`
- `critical_detail_facts.json`
- `qa_code_analysis_playbook.json`

## 当前真实目录结构

```text
<run_root>/
├── 06_knowledge/
│   ├── human_docs/
│   └── machine_index/
├── 08_ai_enrichment/
│   ├── concept_inventory.json
│   ├── concept_relations.json
│   ├── debug_playbook.json
│   ├── verification_playbook.json
│   ├── critical_detail_facts.json
│   ├── qa_code_analysis_playbook.json
│   └── core_concept_type_templates.md
└── 09_source_snapshot/
```

## 如何判断这是当前能力包

看能力特征，不看旧文件名：

1. `machine_index/concept_index.jsonl` 存在
2. `machine_index/question_patterns.json` 存在
3. `kb_manifest.available_ai_artifacts` 中包含 concept/playbook/artifact 信息
4. `doc_catalog.json` 中包含 `core_concept_type_template`，并可能包含 `critical_detail_facts` / `qa_code_analysis_playbook`

## 推荐检索顺序

```text
1. kb_manifest.json
2. doc_catalog.json
3. question_patterns.json
4. fact_index.jsonl / search_index.jsonl
5. concept_index.jsonl / relation_index.jsonl
6. 08_ai_enrichment 中对应对象产物
7. human_docs
8. 09_source_snapshot
```

对精确细节问题，应特别遵循：

```text
critical_detail_facts
  -> question_patterns/detail route
  -> qa_code_analysis_playbook（如仍未 resolved）
  -> minimum source fallback
```
