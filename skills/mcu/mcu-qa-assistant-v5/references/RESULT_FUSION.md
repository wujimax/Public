# Result Fusion

合并多层检索结果，解决知识冲突，生成最终答案。

## Fusion Strategy

```
多层检索结果
    │
    ├─ 第1层: 项目知识库 (最相关)
    │   ├─ 结果1 (score: 5.0)
    │   ├─ 结果2 (score: 4.5)
    │   └─ ...
    │
    ├─ 第2层: 公共知识库 (可复用)
    │   ├─ 结果A (score: 4.0)
    │   ├─ 结果B (score: 3.8)
    │   └─ ...
    │
    └─ 第3层: 网上检索 (补充)
        ├─ 结果X (score: 2.5)
        └─ ...
    │
    ▼
[结果融合器]
    │
    ├─ 冲突检测和解决
    ├─ 置信度加权
    ├─ 相关性排序
    └─ 上下文压缩
    │
    ▼
[最终答案]
```

## Conflict Detection

For V4/V8 project packs, preserve this internal project-source priority for project evidence before mixing in public knowledge:

`machine_index > critical_detail_facts > other_concept_artifacts > human_docs > source_snapshot`

Treat `core_concept_type_templates.md` as a separate explanation scaffold layer, not as a project evidence layer.

For domain protocol or algorithm questions, keep the final answer split into:
- project-proven facts
- general domain knowledge
- inference or uncertainty

### 冲突类型

| 类型 | 示例 | 解决策略 |
|-----|------|---------|
| **API差异** | STM32的`GPIO_Init` vs AT32的`gpio_init` | 标注差异，提供两个版本 |
| **协议参数冲突** | OneNet说用QoS=0，文档说支持QoS=1 | 优先项目实践，标注文档差异 |
| **时序冲突** | 代码说10ms，手册说5ms | 优先代码（实际验证过），标注文档参考 |
| **版本冲突** | 项目用V1.0，公共库有V2.0 | 优先V2.0，保留V1.0作为备选 |

### 冲突解决流程

```python
def resolve_conflicts(results, question_type):
    resolved = []
    conflicts = []

    # 检测冲突
    for i, r1 in enumerate(results):
        for r2 in results[i+1:]:
            if is_conflicting(r1, r2):
                conflicts.append((r1, r2))

    # 解决冲突
    for c in conflicts:
        r1, r2 = c
        resolution = determine_resolution(r1, r2, question_type)

        # 优先保留置信度高的
        if resolution == 'keep_both':
            resolved.append(r1)
            resolved.append(r2)
        elif resolution == 'keep_r1':
            resolved.append(r1)
        else:
            resolved.append(r2)

    # 合并未冲突的结果
    for r in results:
        if r not in [c[0] for c in conflicts] and r not in [c[1] for c in conflicts]:
            resolved.append(r)

    return resolved

def determine_resolution(r1, r2, question_type):
    """根据问题类型决定冲突解决策略"""

    # 项目专属问题：优先项目知识库
    if question_type == 'project_specific':
        return 'keep_r1'  # 假设r1来自项目KB

    # 通用技术问题：优先验证过的知识
    if question_type == 'general_technical':
        # 公共知识库通常经过验证，优先保留
        if r1.source == 'public_kb':
            return 'keep_r1'
        return 'keep_r2'

    # 跨项目迁移：标注差异
    if question_type == 'migration':
        return 'keep_both'  # 保留两个版本供参考

    # 新开发任务：选择更完整的
    if question_type == 'new_development':
        if r1.completeness > r2.completeness:
            return 'keep_r1'
        return 'keep_r2'

    return 'keep_both'
```

## Template-Aware Fusion Rules

When a `concept_index` hit exposes `template_reference` or `template_doc_path`:

1. Open the matching anchor in `08_ai_enrichment/core_concept_type_templates.md` to organize the explanation structure and completeness checklist.
2. Keep all thresholds, state transitions, formulas, register behavior, API names, and debug conclusions grounded in `machine_index`, `human_docs`, or `source_snapshot`.
3. If template wording and project evidence differ, trust the project evidence and explicitly treat template text as generic scaffolding.
4. In compressed context, keep only the matching template heading and a few checklist bullets, not the full template body.

## Confidence Scoring

### 评分因素

| 因素 | 权重 | 说明 |
|-----|-------|------|
| 来源权威性 | 30% | 官方文档 > 项目KB > 公共KB > 网上 |
| 内容相关性 | 25% | 关键词匹配度 |
| 内容完整性 | 20% | 信息的完整程度 |
| 验证状态 | 15% | 是否经过实践验证 |
| 时效性 | 10% | 更新的内容优先 |

### 置信度计算

```python
def calculate_confidence(result, question):
    score = 0

    # 来源权威性 (30%)
    source_weights = {
        'official_docs': 30,
        'project_kb': 25,
        'public_kb': 20,
        'web_search': 10
    }
    score += source_weights.get(result.source, 10)

    # 内容相关性 (25%)
    keyword_match = calculate_keyword_match(result.content, question.keywords)
    score += keyword_match * 25

    # 内容完整性 (20%)
    completeness = calculate_completeness(result.content)
    score += completeness * 20

    # 验证状态 (15%)
    if result.verified:
        score += 15
    elif result.source == 'project_kb':  # 项目KB通常验证过
        score += 10

    # 时效性 (10%)
    days_old = (datetime.now() - result.date).days
    if days_old < 30:
        score += 10
    elif days_old < 180:
        score += 5

    return score / 100  # 归一化到0-1
```

## Relevance Sorting

```python
def sort_by_relevance(fused_results, question):
    """根据问题类型使用不同的排序策略"""

    if question.type == 'project_specific':
        # 项目专属问题：优先项目知识库
        return sorted(fused_results,
                    key=lambda r: (r.source != 'project_kb', -r.confidence))

    elif question.type == 'general_technical':
        # 通用技术问题：优先高置信度
        return sorted(fused_results,
                    key=lambda r: (-r.confidence, r.relevance))

    elif question.type == 'migration':
        # 迁移问题：优先可复用性
        return sorted(fused_results,
                    key=lambda r: (-r.reusability, -r.confidence))

    else:  # new_development
        # 新开发任务：优先完整性和可复用性
        return sorted(fused_results,
                    key=lambda r: (-r.completeness, -r.reusability))
```

## Context Compression

### 压缩策略

```python
def compress_context(fused_results, max_tokens=8000):
    """压缩上下文，控制在token预算内"""

    compressed = []

    # 1. 保留高置信度结果的完整内容
    high_confidence = [r for r in fused_results if r.confidence > 0.8]
    for r in high_confidence[:3]:  # 最多3个
        compressed.append(r)

    # 2. 提取中等置信度结果的关键信息
    medium_confidence = [r for r in fused_results if 0.6 < r.confidence <= 0.8]
    for r in medium_confidence[:5]:  # 最多5个
        compressed.append(extract_key_points(r))

    # 3. 低置信度结果只保留引用
    low_confidence = [r for r in fused_results if r.confidence <= 0.6]
    for r in low_confidence[:10]:  # 最多10个
        compressed.append(create_reference_only(r))

    # 4. 计算token使用
    total_tokens = estimate_tokens(compressed)

    if total_tokens > max_tokens:
        # 超出预算，减少中等置信度
        compressed = high_confidence[:3]
        for r in medium_confidence[:2]:
            compressed.append(extract_key_points(r))
        compressed.extend([create_reference_only(r) for r in low_confidence[:5]])

    return compressed

def extract_key_points(result):
    """从结果中提取关键点"""

    return {
        'type': 'key_points',
        'source': result.source,
        'location': result.location,
        'content': extract_summary(result.content),
        'code_snippet': extract_relevant_code(result.content)
    }

def create_reference_only(result):
    """创建引用-only的结果"""

    return {
        'type': 'reference',
        'source': result.source,
        'location': result.location,
        'content': f"参见: {result.location}",
        'code_snippet': None
    }

def extract_summary(content, max_words=100):
    """提取内容摘要（最多100词）"""
    words = content.split()[:max_words]
    return ' '.join(words) + '...'

def extract_relevant_code(content, question_keywords):
    """提取与问题相关的代码片段"""
    # 根据问题关键词查找相关代码
    return find_relevant_code_snippets(content, question_keywords)
```

---

## Fusion Output Format

```python
class FusedResult:
    def __init__(self):
        self.confidence = 0.0
        self.relevance = 0.0
        self.source = ''
        self.content = ''
        self.location = ''
        self.conflicts = []
        self.notes = []

    def to_markdown(self):
        """转换为Markdown格式输出"""

        return f"""
## 知识来源: {self.source}

**置信度**: {'⭐' * int(self.confidence * 5)}/{self.confidence:.2f}
**相关性**: {'⭐' * int(self.relevance * 5)}/{self.relevance:.2f}
**位置**: `{self.location}`

### 内容摘要
{self.summary}

### 代码引用
```c
{self.code_snippet}
```

### 注意事项
{self.notes}
"""
```

---

## Example Workflow

```python
# 输入：用户问题
question = "项目3中OneNet连接失败怎么排查？"

# Step 1: 问题分类
question_type = classify_question(question)
# 结果: project_specific

# Step 2: 多层检索
layer1_results = search_project_kb(question, project="项目3")
layer2_results = search_public_kb(question, category="OneNet")
layer3_results = search_web(question, context="OneNet NB-IoT")

# Step 3: 结果融合
fused_results = []
fused_results.extend(layer1_results)  # 项目知识库最相关
fused_results.extend(layer2_results)
fused_results.extend(layer3_results)

# Step 4: 冲突检测
resolved = resolve_conflicts(fused_results, question_type)

# Step 5: 置信度评分
for r in resolved:
    r.confidence = calculate_confidence(r, question)

# Step 6: 排序
sorted_results = sort_by_relevance(resolved, question)

# Step 7: 上下文压缩
compressed = compress_context(sorted_results, max_tokens=8000)

# Step 8: 生成答案
answer = generate_answer(compressed)
```

## Exact-Detail Fusion Rules

When `critical_detail_facts.json` is available:

1. If a matched item has `answer_status = resolved`, treat it as the preferred canonical answer for that exact detail.
2. If a matched item is only `value_verified_meaning_needs_analysis`, keep the raw value as evidence but do not overclaim scope, unit, or business meaning.
3. If a matched item is still `needs_second_pass`, treat it as a routing clue, not as a finished answer.
4. If fallback source analysis was required, the final answer must explicitly separate direct evidence, code inference, and remaining uncertainty.
5. If source reasoning resolves a stable repeated question, mention that it should be written back into `critical_detail_facts.json` or `qa_code_analysis_playbook.json`.

