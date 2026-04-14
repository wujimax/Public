# Code Analysis Fallback

Use this reference when project evidence inside the knowledge pack is not yet sufficient.

## Entry Conditions

Enter fallback mode only when one or more of these is true:

- `critical_detail_facts.json` has no matching resolved answer
- the pack has conflicting detail values
- the user asks for the derivation chain, and the current docs do not prove it
- a concept object exists, but the exact numeric detail or trigger chain is still unresolved

## Route Selection

1. Read `doc_catalog.json` and `question_patterns.json`.
2. Open `critical_detail_facts.json` first for exact-value questions.
3. Open `qa_code_analysis_playbook.json` and choose the closest `family_id`.
4. Use that playbook's `preferred_indexes`, `preferred_doc_types`, `preferred_files`, and `preferred_symbols` as constraints.
5. Only then open the minimum files needed from `09_source_snapshot`.

## Analysis Discipline

1. Lock the current target scope before tracing code.
2. Prefer the smallest proof chain that answers the user question.
3. Distinguish raw literal values from real-world units and semantics.
4. Distinguish compile-time constants, persisted parameters, runtime counters, and derived values.
5. When multiple similar values exist, say what each one applies to and what must not be confused.
6. If the chain cannot be fully proven, stop at the last proven hop and mark the rest as uncertainty.

## Output Discipline

Always separate these parts in the answer when fallback mode was used:

- Direct answer
- Evidence
- Code inference
- Uncertainty
- Suggested write-back candidate

## Never Do This

- Do not free-scan the entire source tree.
- Do not claim certainty without file/function anchors.
- Do not convert `needs_second_pass` into a resolved fact on your own.
- Do not let comments override current target code.
