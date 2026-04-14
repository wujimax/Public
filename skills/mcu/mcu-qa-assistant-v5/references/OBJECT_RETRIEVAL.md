# 对象级检索策略（当前真实 v8 对齐版）

最后更新：2026-03-21
版本：V4

这份文档定义的“对象级检索”，不再是旧版 V3 里那套：

- `knowledge_objects.jsonl`
- `knowledge_relations.jsonl`
- `cross_cutting_evaluations.jsonl`

当前真实 v8 的对象级检索，核心应该是：

```text
问题
  -> question_patterns 路由提示（可选）
  -> concept_index 概念对象命中
  -> relation_index / concept_relations 关系扩展
  -> debug_playbook / verification_playbook 调试验证扩展
  -> template_reference 对应模板脚手架
  -> human_docs 语义补充
  -> source_snapshot 代码回退
```

## 1. 当前真实对象入口

### 主入口：`machine_index/concept_index.jsonl`

每条记录都可以视为“项目概念对象”的索引入口。
当前真实样例里的 concept 记录通常包含这些字段：

| 字段 | 作用 | 用法 |
|-----|------|------|
| `id` / `concept_id` | 对象唯一标识 | 作为后续关系、playbook 关联键 |
| `concept_type` | 对象类型 | 例如 `protocol`、`algorithm`、`timing_path`、`framework_mechanism`、`driver`、`feature`、`fault_policy`、`diagnostic_interface` |
| `canonical_name` / `title` | 主名称 | 作为回答里的对象主称呼 |
| `aliases` | 别名 | 处理项目缩写、函数名、模块名、行业叫法 |
| `keywords` | 关键词 | 用于召回更多隐式匹配 |
| `summary` | 短摘要 | 用于快速判断是否相关 |
| `code_refs` | 关键源码定位 | 作为强证据锚点 |
| `where_to_read_first` | 首读位置 | 指导源码回退顺序 |
| `critical_functions` | 关键函数 | 适合调试入口、调用链说明 |
| `critical_variables` | 关键变量/参数 | 适合阈值、状态、时序问题 |
| `focus_questions` | 该对象天然回答的问题 | 帮助组织解释结构 |
| `debug_playbook_ids` | 调试手册关联 | 跳去 `debug_playbook.json` |
| `verification_ids` | 验证手册关联 | 跳去 `verification_playbook.json` |
| `template_reference` / `template_doc_path` | 模板锚点 | 用于 template-aware 解释 |
| `evidence_status` | 证据状态 | 例如 `verified_by_code`、`heuristic_only` |
| `standard_family` / `standard_mapping_status` | 标准映射状态 | 判断是否仍需要 second-pass 深挖 |

### 旧版 V3 不该再用的入口

不要再把下面这些当主入口：

- `knowledge_objects.jsonl`
- `knowledge_relations.jsonl`
- `cross_cutting_evaluations.jsonl`

当前真实 v8 并不以这些文件作为交付主结构。

## 2. 什么问题应该先走对象检索

以下问题优先走 concept-first：

| 问题类型 | 典型问法 | 优先 concept_type |
|---------|---------|-------------------|
| 协议类 | “EV1527 时序怎么走？” | `protocol` |
| 算法类 | “这个判定规则怎么实现？” | `algorithm` |
| 时序类 | “这条链路是谁触发的？” | `timing_path` |
| 框架类 | “任务和中断挂在哪个框架上？” | `framework_mechanism` |
| 调试入口类 | “应该先在哪打断点？” | `diagnostic_interface` / `fault_policy` |
| 功能类 | “这个业务功能在哪落地？” | `feature` |
| 驱动类 | “OLED 驱动初始化在哪？” | `driver` |

如果问题已经明显是协议、算法、时序、框架这四类之一，优先顺序应该是：

1. `question_patterns.json`（如果需要路线提示）
2. `concept_index.jsonl`
3. `relation_index.jsonl`
4. `08_ai_enrichment/concept_relations.json`
5. `debug_playbook.json` / `verification_playbook.json`
6. `core_concept_type_templates.md`
7. `human_docs`
8. `09_source_snapshot`

## 3. `question_patterns.json` 的使用方式

当前真实 v8 多了一层路由提示：`machine_index/question_patterns.json`。

样例里会给出类似：

- `qp_protocol_001`
- `qp_algorithm_001`
- `qp_timing_001`
- `qp_framework_001`

每个 pattern 都会给：

- `preferred_indexes`
- `preferred_doc_types`

用法是：

1. 先根据用户问题归类到某个 pattern 家族
2. 用 `preferred_indexes` 决定先开哪些索引
3. 用 `preferred_doc_types` 决定后续优先开哪些文档类型

注意：
`question_patterns.json` 只是“检索路线提示”，不是证据来源。

## 4. concept 命中的评分与判断

命中 `concept_index.jsonl` 时，优先看这些字段：

### 4.1 身份相关字段

- `concept_type`
- `canonical_name`
- `aliases`
- `keywords`

这决定“它是不是用户问的那个对象”。

### 4.2 证据强度字段

- `evidence_status`
- `code_refs`
- `where_to_read_first`
- `critical_functions`
- `critical_variables`

这决定“它能不能直接支撑结论”。

### 4.3 深挖相关字段

- `focus_questions`
- `debug_playbook_ids`
- `verification_ids`
- `standard_mapping_status`
- `expected_outputs`

这决定“还要不要继续展开”。

### 4.4 置信度处理建议

| `evidence_status` | 含义 | 回答策略 |
|------------------|------|---------|
| `verified_by_code` | 已有较强代码证据 | 可以直接作为项目已证实内容 |
| `heuristic_only` | 仍偏启发式识别 | 需要补查 `human_docs` 或 `source_snapshot` |
| 其他/缺失 | 证据状态不清晰 | 明确标注不确定性 |

## 5. 关系扩展怎么做

### 关系来源

当前真实 v8 的关系层通常来自两处：

1. `machine_index/relation_index.jsonl`
2. `08_ai_enrichment/concept_relations.json`

可以把它理解为：

- `relation_index.jsonl` 更适合做快速关系召回
- `concept_relations.json` 更适合做概念对象之间的补充关系解释

### 关系扩展目标

当你命中一个 concept 后，下一步通常要补这些问题：

- 它依赖谁
- 谁触发它
- 它影响谁
- 它的数据从哪里来、到哪里去
- 它的调试入口和验证入口分别在哪

### 典型场景

问题：`EV1527 解码失败会影响什么？`

正确做法：

1. 命中 `protocol` 或 `algorithm` 相关 concept
2. 用 `relation_index` / `concept_relations` 查：
   - 上游输入
   - 下游事件
   - 关联功能
3. 再用 `debug_playbook` 查调试入口
4. 再补 `05_领域协议与算法.md` 或 `09_控制流分析.md`

## 6. playbook 扩展怎么做

### 调试入口

如果 concept 记录带有：

- `debug_playbook_ids`

就应该去 `08_ai_enrichment/debug_playbook.json` 展开。

优先提取：

- 推荐断点
- 推荐观察变量
- 典型故障入口
- 排查顺序
- 所需工具

### 验证入口

如果 concept 记录带有：

- `verification_ids`

就应该去 `08_ai_enrichment/verification_playbook.json` 展开。

优先提取：

- 验证前提
- 验证步骤
- 预期现象
- 风险点
- 失败时的回退动作

### 替代了什么

这套 playbook 机制，实际上替代了旧版 V3 想象中的：

- `13_调试指南.md`
- 部分“横切评估”文件职责

所以在当前真实 v8 里，调试问题不应再默认去找旧文档名，而应先看 concept 命中是否带 playbook 关联。

## 7. template-aware 检索怎么做

### 什么时候启用模板

当 concept 命中记录带有：

- `template_reference`
- `template_doc_path`

就启用 template-aware 检索。

当前真实样例里，最典型的是这些 concept_type：

- `protocol`
- `algorithm`
- `timing_path`
- `framework_mechanism`

它们通常会挂到：

- `08_ai_enrichment/core_concept_type_templates.md#protocol`
- `08_ai_enrichment/core_concept_type_templates.md#algorithm`
- `08_ai_enrichment/core_concept_type_templates.md#timing_path`
- `08_ai_enrichment/core_concept_type_templates.md#framework_mechanism`

### 模板的正确用途

模板用于：

- 组织解释结构
- 提醒哪些检查项不要漏
- 帮助把“标准知识”映射到“项目实现”

模板不能用于：

- 直接代替项目阈值
- 直接代替项目状态机
- 直接代替项目公式
- 直接代替项目寄存器/接口行为
- 直接代替项目调试结论

### 正确顺序

```text
concept 命中
  -> 打开对应模板锚点
  -> 用模板列出该类型应该回答哪些点
  -> 再回到项目索引 / human_docs / source_snapshot 找项目证据
```

### 压缩策略

如果上下文预算紧，只保留：

- 模板标题
- 3-6 条检查项 bullet

不要把整段模板全文塞进上下文。

## 8. `doc_catalog.json` 的作用

对象命中以后，不要盲开文档，先看 `doc_catalog.json`。

它的作用是把 `doc_type` 映射到真实文件路径。

例如当前真实样例里常见：

- `protocol_and_algorithm` -> `human_docs/05_领域协议与算法.md`
- `parameter_index` -> `human_docs/07_关键参数汇总.md`
- `data_flow` -> `human_docs/08_数据流分析.md`
- `control_flow` -> `human_docs/09_控制流分析.md`
- `debug_playbook` -> `08_ai_enrichment/debug_playbook.json`
- `verification_playbook` -> `08_ai_enrichment/verification_playbook.json`
- `core_concept_type_template` -> `08_ai_enrichment/core_concept_type_templates.md`

所以推荐策略是：

1. 先通过 question type 决定目标 `doc_type`
2. 再通过 `doc_catalog.json` 找实际路径
3. 只打开必要文档

## 9. `human_docs` 在对象检索中的位置

`human_docs` 仍然重要，但不再是对象问题的第一入口。

当前真实顺序应该是：

```text
concept_index
  -> relations / playbooks / template
  -> human_docs
```

各类问题常见的 `human_docs` 补充路径：

| 问题类型 | 常补文档 |
|---------|---------|
| 协议类 | `05_领域协议与算法.md`、`07_关键参数汇总.md` |
| 算法类 | `05_领域协议与算法.md`、`07_关键参数汇总.md`、`09_控制流分析.md` |
| 时序类 | `09_控制流分析.md`、`08_数据流分析.md` |
| 框架类 | `03_系统架构.md`、`09_控制流分析.md` |
| 调试类 | `11_项目最常见的20个问题.md` |
| 功能类 | `04_功能模块.md`、`06_功能索引.md` |

## 10. 什么时候回退到源码快照

只有这些情况才回退到 `09_source_snapshot`：

1. concept 命中是 `heuristic_only`
2. human_docs 只给了结论，没有实现细节
3. 需要确认真实状态切换、时序阈值、公式、寄存器行为、API 调用链
4. 需要确认注释和代码哪个是真的

源码快照优先顺序：

1. `active_target_sources/`
2. `key_headers/`
3. `build_files/`

不要一上来就扫整包源码。
应优先使用 concept 里的：

- `where_to_read_first`
- `critical_functions`
- `critical_variables`
- `code_refs`

来缩小范围。

## 11. 当前真实 v8 下的完整对象检索流程

问题：`这个项目里的 EV1527 解码为什么容易误判？`

推荐流程：

1. 从 `question_patterns.json` 判断这属于协议/算法类
2. 在 `concept_index.jsonl` 中找 `protocol` / `algorithm` 相关对象
3. 优先看：
   - `aliases`
   - `keywords`
   - `summary`
   - `evidence_status`
   - `code_refs`
4. 若 concept 带 `template_reference`，先开对应模板锚点
5. 再开 `relation_index.jsonl` 和 `concept_relations.json` 查上下游关系
6. 再看 `debug_playbook.json` 提取断点、变量、排查链
7. 再补 `05_领域协议与算法.md`、`07_关键参数汇总.md`、`09_控制流分析.md`
8. 若关键阈值或状态机仍不清楚，再去 `09_source_snapshot`
9. 最终回答分成：
   - 项目已证实
   - 通用协议背景
   - 推断与不确定点

## 12. 硬规则

1. 对象入口以 `concept_index.jsonl` 为准，不再以旧 flat V8 文件为准。
2. `question_patterns.json` 只负责路由，不负责给证据。
3. `core_concept_type_templates.md` 只负责脚手架，不负责给项目事实。
4. 调试/验证问题先看 playbook 关联，不要先假设存在旧调试总文档。
5. 如果 `search_index` 没命中精确词，不要立刻判定知识库缺失。
6. 当代码、注释、文档冲突时，以当前目标源码行为为准。

## 13. 结论

当前真实 v8 的“对象级检索”本质上已经变成：

- `concept_index` 负责对象识别
- `question_patterns` 负责路线提示
- `relation_index + concept_relations` 负责关系扩展
- `debug_playbook + verification_playbook` 负责调试验证入口
- `core_concept_type_templates` 负责解释脚手架
- `human_docs + source_snapshot` 负责补足项目证据

这才是 `mcu-qa-assistant-v5` 应该对齐的对象检索模型。
