# Layered Retrieval Strategy

分层检索策略，按优先级搜索不同知识源，确保答案准确性和完整性。

## Retrieval Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  智能分层检索系统                                   │
├─────────────────────────────────────────────────────────────┤
│                                                          │
│  用户提问                                               │
│    ↓                                                   │
│  [问题分类器]                                         │
│    ├─ 问题类型识别                                      │
│    ├─ 关键词提取                                        │
│    └─ 检索范围确定                                    │
│    ↓                                                   │
│  ┌─────────────────────────────────────────────┐            │
│  │ 第1层: 项目知识库 (最相关)              │            │
│  ├─ 搜索所有项目的结构化文档                   │            │
│  ├─ 查找功能模块、数据流、控制流                      │            │
│  └─ 限制5个最相关结果                               │            │
│  │                                             │            │
│  ┌─────────────────────────────────────────────┐            │
│  │ 第2层: 公共知识库 (可复用)              │            │
│  ├─ 协议库 (MQTT/OneNet/EV1527)             │            │
│  ├─ 算法库 (CRC/滤波/PID)                  │            │
│  ├─ 架构库 (设计模式/OS)                   │            │
│  ├─ 外围驱动库 (OLED/传感器/存储)             │            │
│  └─ 厂商库 (STM32/AT32)                     │            │
│  │                                             │            │
│  ┌─────────────────────────────────────────────┐            │
│  │ 第3层: 网上检索 (补充知识)                │            │
│  ├─ 官方文档搜索                                    │            │
│  ├─ 技术论坛搜索                                    │            │
│  └─ GitHub/开源项目搜索                             │            │
│  └─────────────────────────────────────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Project Knowledge Base

### V10 Flat MD 知识包（Layout C）

如果输入的是 `mcu-project-organizer-v10` 生成的扁平 MD 知识包（目录下有 `00_阅读指南.md`，没有 `machine_index/`）：

1. 先对问题分类，确定目标检索域
2. 根据下表确定优先读取的文档：

| 问题类型 | 首选文档 | 补充文档 |
|---|---|---|
| 精确参数（波特率/时钟/超时/阈值） | `06_关键参数表.md` | `02_硬件配置.md` |
| 引脚/GPIO/外设配置 | `02_硬件配置.md` | `06_关键参数表.md` |
| 协议/帧格式/AT指令 | `05_通信协议.md` | `06_关键参数表.md` |
| 任务/调度/中断/启动流程 | `03_系统架构.md` | `04_功能模块.md` |
| 模块职责/函数/API位置 | `04_功能模块.md` | `03_系统架构.md` |
| Bug/问题排查/风险 | `07_已知问题与建议.md` | `04_功能模块.md` |
| 产品功能/概况 | `01_项目介绍.md` | `00_阅读指南.md` |

3. 读首选文档中的相关章节
4. 如果首选不够，再读补充文档
5. 如果仍不够，扫描剩余文档
6. V10 文档中标注了 `源文件:行号` 的内容视为代码已验证证据
7. V10 文档中标注了 ⚠️ 的内容需要在回答中保留不确定性
8. 不要尝试打开 `machine_index/`、`08_ai_enrichment/` 或 `09_source_snapshot/`

### V11 知识包（Layout D）

如果输入的是 `mcu-project-organizer-v11` 生成的知识包（目录下有 `00_阅读指南.md` 且有 `_v10_snapshot/sources/`）：

1. 先按 Layout C 的路由表检索知识库文档（步骤1-6同上）
2. 如果知识库文档无法完全回答问题，进入**受控源码回退**：
   a. 从知识库文档中提取相关的源文件名和函数名
   b. 仅读取 `_v10_snapshot/sources/` 中对应的文件（最多3个）
   c. 遵循 `V11_SOURCE_FALLBACK_ADDENDUM.md` 中的纪律约束
   d. 回答中必须区分知识库证据、源码验证、推断和不确定点
3. 如果源码也不足，再回退到公共知识库或网搜

### 当前 V4/V6/V8 知识包优先顺序（Layout B）

如果输入的是当前 V4/V6/V8 知识包：

1. 先读 `machine_index/kb_manifest.json`
2. 再读 `machine_index/doc_catalog.json`
3. 如果存在 `question_patterns.json`，先把它当作检索路线提示，尤其是协议、算法、时序、框架类问题。
4. 优先检索：
   - `concept_index.jsonl`（如果存在，优先用于协议、算法、时序、框架、调试入口类问题）
   - `fact_index.jsonl`
   - `search_index.jsonl`
   - `relation_index.jsonl`
   - 如果 `concept_index.jsonl` 命中的对象带有 `template_reference` 或 `template_doc_path`，先打开 `08_ai_enrichment/core_concept_type_templates.md` 中对应模板，再决定是否进入长篇 `human_docs`
5. 有需要时再补：
   - `inference_index.jsonl`
   - `advice_index.jsonl`
   - `entity_index.json`
   - `evidence_refs.jsonl`
6. 如果 `doc_catalog.json` 提示存在 `concept_inventory`、`concept_relations`、`deep_dive_queue`、`debug_playbook`、`verification_playbook`、`core_concept_type_template`，在打开长篇 `human_docs` 前优先读这些对象化 AI artifacts。
7. `core_concept_type_template` 只能作为解释脚手架和检查清单，不能替代项目证据；最终结论仍必须回到项目索引、文档或源码。
8. 只有在索引、`question_patterns` 路由提示和对象化 artifacts 都不足时，才打开对应 `human_docs`
9. 如果 `human_docs` 仍不足，再回退到 `09_source_snapshot`
10. 对协议、编码、行业算法或判定逻辑问题，如果精确关键词没有命中 `search_index.jsonl`，仍要检查 `doc_catalog.json` 中的 `concept_inventory`、`concept_relations`、`debug_playbook`、`verification_playbook`、`core_concept_type_template`、`protocol_and_algorithm`、`parameter_index`、`data_flow`、`control_flow`，不要直接判定为知识库缺口。
### 检索目标

| 文档类型 | 搜索内容 | 相关性权重 |
|---------|---------|-----------|
| 00_项目索引_地图.md | 项目概览、文件结构 | ⭐⭐⭐⭐⭐ |
| 01_硬件配置.md | 外设配置、引脚定义 | ⭐⭐⭐⭐ |
| 03_系统架构.md | 分层架构、模块关系 | ⭐⭐⭐⭐⭐ |
| 04_功能模块.md | 功能实现、代码位置 | ⭐⭐⭐⭐⭐ |
| 05_领域协议与算法.md | 领域协议、编码规则、行业算法 | ⭐⭐⭐⭐⭐ |
| 07_关键参数汇总.md | 阈值、时基、帧长、公式参数 | ⭐⭐⭐⭐ |
| 08_数据流分析.md | 数据流向、转换 | ⭐⭐⭐⭐ |
| 09_控制流分析.md | 控制流程、状态机 | ⭐⭐⭐⭐ |
| 11_项目最常见的20个问题.md | 项目常见问题、调试切入口 | ⭐⭐⭐⭐ |

### 检索策略

```python
# 搜索关键词生成
def generate_search_keywords(question):
    keywords = []

    # 提取核心功能词
    if "OneNet" in question:
        keywords.extend(["OneNet", "MQTT", "183.230.40.96"])
    if "EV1527" in question:
        keywords.extend(["EV1527", "433", "门磁", "编码"])

    # 提取动作词
    if "连接" in question or "初始化" in question:
        keywords.extend(["初始化", "连接", "配置", "setup"])
    if "发送" in question or "上报" in question:
        keywords.extend(["发送", "上报", "publish", "send"])

    return keywords

# 文档权重计算
def calculate_relevance_score(doc_name, keywords):
    score = 0

    # 文档名匹配
    if any(kw in doc_name for kw in keywords):
        score += 3

    # 文档类型权重
    if doc_name in high_relevance_docs:
        score += 5
    elif doc_name in medium_relevance_docs:
        score += 3

    return score

# 检索执行
def search_project_kb(question):
    keywords = generate_search_keywords(question)

    results = []
    for doc in project_documents:
        score = calculate_relevance_score(doc.name, keywords)
        if score > 0:
            results.append((doc, score))

    # 按分数排序，限制前5个
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]
```

### 结果格式

```markdown
## 第1层: 项目知识库检索结果

### [项目X] - [文档名称]

**相关性**: ⭐⭐⭐⭐⭐ (5/5)

**核心内容**:
[文档主要内容摘要]

**关键位置**:
- 功能模块: `文件名:行号范围`
- 代码位置: `文件.c:函数名`

**相关引用**:
- 依赖文档: `文档名称`
- 关联功能: `功能名称`
```

---

## Layer 2: Public Knowledge Base

### 检索目标

| 知识库 | 搜索内容 | 可复用性 |
|--------|---------|----------|
| 07_协议库/ | MQTT/HTTP/IoT平台/私有协议 | 90-100% |
| 06_算法库/ | CRC/滤波/数据结构/状态机 | 100% |
| 08_架构库/ | 分层架构/调度/消息机制 | 80-95% |
| 02-05_模块库/ | 通信/传感器/显示/存储驱动 | 80-90% |
| 01_MCU厂商库/ | STM32/AT32/GD32 HAL库 | 60-80% |

### 检索策略

```python
def search_public_kb(question, question_type):
    results = []

    # 根据问题类型确定搜索类别
    if question_type == "协议相关问题":
        categories = ["07_协议库/", "02_通信模块库/"]
    elif question_type == "算法相关问题":
        categories = ["06_算法库/"]
    elif question_type == "架构相关问题":
        categories = ["08_架构库/"]
    elif question_type == "驱动相关问题":
        categories = ["02-05_模块库/"]
    else:
        # 通用问题，搜索所有
        categories = ["06_算法库/", "07_协议库/", "08_架构库/"]

    # 在指定类别中搜索
    for category in categories:
        for item in public_kb[category]:
            relevance = calculate_kb_relevance(question, item)
            if relevance > 0.7:  # 只保留高相关性
                results.append((item, relevance))

    return results
```

### 结果格式

```markdown
## 第2层: 公共知识库检索结果

### [知识名称] - [知识类型]

**相关性**: ⭐⭐⭐⭐ (4/5)
**可复用性**: 100% (硬件无关)

**核心内容**:
[知识核心描述]

**实现位置**:
- 源代码: `公共知识库/类别/文件.c`
- 文档: `公共知识库/类别/文档.md`

**使用说明**:
[如何使用这个知识]
```

---

## Layer 3: Web Retrieval

### 检索策略

```python
def search_web(query, context):
    # 生成搜索查询
    search_queries = []

    # 官方文档查询
    search_queries.append({
        'query': f"{context} 官方文档",
        'source': 'official'
    })

    # API参考查询
    search_queries.append({
        'query': f"{context} API reference",
        'source': 'official'
    })

    # 示例代码查询
    search_queries.append({
        'query': f"{context} example code",
        'source': 'github'
    })

    # 问题排查查询
    search_queries.append({
        'query': f"{context} 问题解决",
        'source': 'forum'
    })

    return search_queries
```

### 优先级排序

| 来源 | 优先级 | 置信度 |
|------|--------|-------|
| 官方文档 | ⭐⭐⭐⭐⭐ | 高 |
| 官方示例代码 | ⭐⭐⭐⭐ | 高 |
| GitHub仓库 | ⭐⭐⭐ | 中 |
| 技术论坛 | ⭐⭐ | 中 |
| 其他网站 | ⭐ | 低 |

### 结果过滤

过滤条件：
- [ ] 来源权威性（官方 > 论坛）
- [ ] 内容时效性（最新 > 旧版）
- [ ] 相关性评分
- [ ] 代码可验证性

---

## Retriever Integration

```python
class LayeredRetriever:
    def __init__(self, project_kb, public_kb):
        self.project_kb = project_kb
        self.public_kb = public_kb

    def retrieve(self, question):
        # 第1层: 项目知识库
        layer1_results = self.search_project_kb(question)

        # 第2层: 公共知识库
        question_type = self.classify_question(question)
        layer2_results = self.search_public_kb(question, question_type)

        # 第3层: 网上检索（如果需要）
        layer3_results = []
        if self.need_web_search(layer1_results, layer2_results, question):
            layer3_results = self.search_web(question)

        # 合并结果
        all_results = {
            'layer1': layer1_results,
            'layer2': layer2_results,
            'layer3': layer3_results
        }

        return all_results

    def need_web_search(self, l1_results, l2_results, question):
        # 判断是否需要网搜
        if len(l1_results) > 0 and len(l2_results) > 0:
            return False  # 已有足够知识

        # 检查知识覆盖度
        coverage = self.calculate_coverage(l1_results, l2_results, question)
        if coverage < 0.7:  # 覆盖度低于70%
            return True

        return False
```

---

## Performance Optimization

### 缓存策略

```python
class RetrieverCache:
    def __init__(self):
        self.cache = {}
        self.max_size = 1000

    def get(self, query_hash):
        return self.cache.get(query_hash)

    def set(self, query_hash, results):
        if len(self.cache) >= self.max_size:
            # LRU淘汰
            oldest = min(self.cache.items(), key=lambda x: x[1].timestamp)
            del self.cache[oldest[0]]

        self.cache[query_hash] = {
            'results': results,
            'timestamp': time.time()
        }
```

### 并行检索

```python
async def parallel_retrieve(queries):
    # 并行执行多层检索
    tasks = [
        search_project_kb(query),
        search_public_kb(query),
        search_web(query)
    ]

    results = await asyncio.gather(*tasks)
    return results
```

## Exact-Detail And Fallback Rules

For questions like timebase, timeout, retry count, threshold, default value, or exact period:

1. If `doc_catalog.json` exposes `critical_detail_facts`, open `08_ai_enrichment/critical_detail_facts.json` first.
2. If the matching item is `resolved`, answer from it before opening long human docs.
3. If the item is not resolved, open `08_ai_enrichment/qa_code_analysis_playbook.json` and choose the closest question family.
4. Only when that playbook still requires more evidence should you enter `09_source_snapshot` for targeted source analysis.
5. After fallback analysis, explicitly mark which parts are direct evidence, which are code inference, and which remain uncertain.

