# Question Classifier

Question classification determines the retrieval strategy and knowledge sources.

Before classifying a project-specific question, first resolve the project KB layout from `PROJECT_PACK_LAYOUT.md`.

## Classification Hierarchy

```
用户问题
    │
    ├─ 问题类型判断
    │   ├─ 项目专属问题
    │   ├─ 通用技术问题
    │   ├─ 跨项目迁移
    │   └─ 新开发任务
    │
    ├─ 知识层次判断
    │   ├─ 硬件配置层
    │   ├─ 协议层
    │   ├─ 算法层
    │   ├─ 架构层
    │   └─ 外围驱动层
    │
    └─ 检索范围确定
        ├─ 项目知识库
        ├─ 公共知识库
        └─ 网上检索
```

## Type 1: Project-Specific Questions

**识别模式**:

| 关键词 | 示例问题 | 检索优先级 |
|--------|-----------|------------|
| 项目名 + 功能/问题 | "项目3的OneNet连接失败" | 项目KB > 公共KB > 代码 |
| 项目名 + 位置 | "项目1的CRC函数在哪？" | 项目KB > 代码 |
| 项目名 + 错误 | "项目2编译报错xxx" | 项目KB > 代码 > 网上 |
| 项目名 + 调试 | "项目5的状态机调试" | 项目KB > 公共KB > 代码 |

**检索策略**:
1. **第1层**: 项目知识库

   **Layout C (V10 Flat MD)**:
   - 先判断知识包布局。如果目录下有 `00_阅读指南.md`、没有 `machine_index/`，则为 Layout C。
   - 按 `V10_FLAT_MD_ADDENDUM.md` 的路由表确定首选和补充文档。
   - 精确参数→`06_关键参数表.md`；硬件→`02_硬件配置.md`；协议→`05_通信协议.md`；架构→`03_系统架构.md`；模块→`04_功能模块.md`；Bug→`07_已知问题与建议.md`
   - 不要尝试打开 `machine_index/`、`08_ai_enrichment/`
   - V10 文档中的 `源文件:行号` 引用视为代码已验证证据

   **Layout B (V4/V6/V8)**:
   - **注意**: 如果目录下有 `00_阅读指南.md` 且有 `_v10_snapshot/sources/`，则为 **Layout D**（V11），先按 Layout C 路径检索知识库文档，不够时可进入受控源码回退（仅读取 `_v10_snapshot/sources/` 中对应文件，最多3个，遵循 `V11_SOURCE_FALLBACK_ADDENDUM.md`），回答中区分知识库证据和源码验证。
   - 如果是当前 V4/V6/V8 知识包，先读 `machine_index/kb_manifest.json` 和 `machine_index/doc_catalog.json`
   - 对协议、算法、时序、框架、调试入口类问题，先看 `question_patterns.json` 给出的 `preferred_indexes` / `preferred_doc_types`，再检索 `concept_index.jsonl`
   - 如果 `concept_index.jsonl` 命中的对象带有 `template_reference` 或 `template_doc_path`，先打开 `08_ai_enrichment/core_concept_type_templates.md` 对应模板，再决定是否进入长篇 `human_docs`
   - 再检索 `fact_index.jsonl`、`search_index.jsonl`、`relation_index.jsonl`
   - 如果 `doc_catalog.json` 暗示存在 `concept_inventory`、`concept_relations`、`debug_playbook`、`verification_playbook`、`core_concept_type_template`，优先打开这些对象化 AI artifacts
   - 只有在索引不足时，才打开相关 `human_docs`
   - 如果 `human_docs` 仍不足，再回退到 `09_source_snapshot`
   - 限制 5 个最相关结果，不做全量展开

2. **第2层**: 公共知识库
   - 根据问题类型检索相关类别
   - 如OneNet问题 → `07_协议库/OneNet/`
   - 如架构问题 → `08_架构库/`

3. **第3层**: 原始源代码
   - 定位具体文件和函数
   - 阅读代码实现

### 特殊情况：项目内的领域协议/算法问题

**示例**:
- "EV1527协议时序是怎样的？"
- "这个项目里的2262语义是怎么裁剪出来的？"
- "这个行业算法为什么这样判定？"
- "CRC或滤波阈值在项目里是怎么落地的？"

**额外规则**:
1. 先判断这是不是"项目里的领域规则实现"，而不是纯通用算法问答。
2. 先查 `question_patterns.json`，确认这是不是协议/算法/时序/框架类路线，再查 `concept_index.jsonl` 和 `relation_index.jsonl`，确认对象身份、触发链、依赖链、调试入口。
3. 如果命中的概念对象带有 `template_reference` 或 `template_doc_path`，先打开 `08_ai_enrichment/core_concept_type_templates.md` 对应模板，用它组织解释结构和检查项，但不要把模板内容当作项目证据。
4. 不要因为 `search_index.jsonl` 没有精确关键词就立刻判定为知识库缺口。
5. 先开 `doc_catalog.json`，优先看 `concept_inventory`、`concept_relations`、`debug_playbook`、`verification_playbook`、`core_concept_type_template`、`protocol_and_algorithm`、`parameter_index`、`data_flow`、`control_flow`。
6. 如果 `human_docs` 里只有实现痕迹没有完整原理，再去 `09_source_snapshot` 找 `decode/encode/filter/match/compute/proto/rfd/mqtt` 一类文件。
7. 最终输出必须分清：
   - 项目已证实的实现约束
   - 行业通用协议/算法背景
   - 推断与不确定点
8. 若项目中只能证明"阈值/公式/兼容层"，不能冒充成"项目完整记录了该行业知识说明"。


---

## Type 2: General Technical Questions

**识别模式**:

| 关键词 | 示例问题 | 检索优先级 |
|--------|-----------|------------|
| 协议名 + 如何实现 | "如何实现MQTT连接？" | 公共KB > 项目KB > 网上 |
| 芯片名 + 驱动 | "SSD1306如何初始化？" | 公共KB > 网上 |
| 算法名 + 实现 | "如何实现CRC16？" | 公共KB > 网上 |
| 架构模式 + 设计 | "如何设计三层架构？" | 公共KB > 网上 |

**检索策略**:
1. **第1层**: 公共知识库
   - 搜索对应类别的完整文档
   - 查找实现代码和示例
   - 查找API参考

2. **第2层**: 项目知识库
   - 查找实际使用案例
   - 对比多个项目实现
   - 提取最佳实践

3. **第3层**: 网上检索
   - 查找官方文档
   - 查找官方示例代码
   - 验证信息准确性

---

## Type 3: Cross-Project Migration

**识别模式**:

| 关键词 | 示例问题 | 检索优先级 |
|--------|-----------|------------|
| 迁移 + MCU名称 | "如何迁移到AT32？" | 源项目KB > 公共KB > 新MCU文档 |
| 适配 + 芯片 | "STM32的I2C和AT32的区别？" | 源项目KB > 新MCU文档 |
| 复用 + 知识类型 | "EV1527代码能复用吗？" | 源项目KB > 公共KB |
| 替换 + 组件 | "用XX替换YY需要改什么？" | 源项目KB > 新MCU文档 |

**检索策略**:
1. **第1层**: 源项目知识库
   - 查找 `13_可复用知识索引.md`
   - 提取硬件无关部分
   - 定位需要适配的部分

2. **第2层**: 公共知识库
   - 协议/算法: 100%可复用
   - 架构: 80-95%可复用
   - 对比API差异

3. **第3层**: 新MCU官方资源
   - 查找新MCU HAL库文档
   - 查找API对比表
   - 查找迁移示例

---

## Type 4: New Development Tasks

**识别模式**:

| 关键词 | 示例问题 | 检索优先级 |
|--------|-----------|------------|
| 开发 + 模块 | "开发OneNet模块" | 公共KB > 项目KB > 网上 |
| 实现 + 芯片 | "实现OLED显示" | 公共KB > 网上 |
| 设计 + 系统 | "设计报警系统" | 公共KB > 项目KB |
| 实现 + 协议 | "实现MQTT连接" | 公共KB > 网上 |

**检索策略**:
1. **第1层**: 公共知识库
   - 查找完整方案模板
   - 查找驱动代码
   - 查找架构设计

2. **第2层**: 项目知识库
   - 查找类似项目实现
   - 提取架构模式
   - 提取项目常见问题与调试切入点

3. **第3层**: 网上检索
   - 新MCU的HAL库
   - 参考手册和示例代码

---

## Knowledge Level Mapping

| 知识层次 | 公共库位置 | 关键词 | 硬件相关 |
|-----------|------------|---------|-----------|
| 协议层 | 07_协议库/ | MQTT/HTTP/UART/I2C/OneNet | 低 (0-20%) |
| 算法层 | 06_算法库/ | CRC/滤波/队列/状态机 | 无 (0%) |
| 架构层 | 08_架构库/ | 分层/调度/消息 | 低 (10-20%) |
| 驱动层 | 02-05_模块库/ | OLED/传感器/存储 | 中 (20-40%) |
| 厂商库 | 01_MCU厂商库/ | STM32/AT32/GD32库 | 高 (80-100%) |

---

## Confidence Scoring

对每个检索结果评估置信度：

| 得分 | 说明 | 优先级 |
|-----|------|-------|
| 1.0 | 官方文档/验证过的代码 | 最高 |
| 0.9 | 项目知识库 + 详细说明 | 高 |
| 0.8 | 公共知识库 + 完整实现 | 高 |
| 0.7 | 公共知识库 + 简要说明 | 中 |
| 0.6 | 网上搜索 + 官方来源 | 中 |
| 0.5 | 网上搜索 + 非官方来源 | 低 |

置信度用于：
- 结果排序
- 知识冲突解决（优先高置信度）
- 答案准确性评估

## Exact-Detail Questions And Evidence Gaps

Examples:
- "What is the project timebase?"
- "What is the timeout here?"
- "What is the default value?"
- "Why is this 10ms instead of 1ms?"

Rules:
1. If `doc_catalog.json` exposes `critical_detail_facts`, open `08_ai_enrichment/critical_detail_facts.json` first.
2. If a matching detail item has `answer_status = resolved`, prefer it over long-form human-doc paraphrases.
3. If a detail item only proves the raw value, explicitly say that the value is verified but the meaning/unit still needs code-chain confirmation.
4. If no detail item matches, or the item is still `needs_second_pass`, enter `qa_code_analysis_playbook.json` constrained source analysis.
5. During fallback analysis, output must distinguish direct evidence, code inference, and remaining uncertainty.
6. If the derived answer is stable and high-value, mention that it should be written back into `critical_detail_facts.json` or `qa_code_analysis_playbook.json`.

