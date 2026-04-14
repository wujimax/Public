# Context Compression

控制上下文长度，确保在token预算内生成高质量答案。

## Context Budget

| 资源 | Token预算 | 说明 |
|--------|-----------|------|
| 系统提示词 | ~2000 | Claude的系统指令 |
| Skill提示词 | ~5000 | 当前Skill的说明 |
| 用户问题 | ~500 | 用户原始问题 |
| **知识检索** | ~4000 | 各层检索结果 |
| 答案生成 | ~8000 | Claude推理和生成 |
| **总计** | ~20000 | Claude上下文窗口上限 |

**压缩目标**：将知识检索结果压缩到 ~4000 tokens

---

## Compression Strategy

```
原始检索结果 (假设8000 tokens)
    │
    ├─ 第1层: 项目知识库 (2500 tokens)
    │   ├─ 00_项目索引: 200 tokens
    │   ├─ 01_硬件配置: 300 tokens
    │   ├─ 03_功能模块: 800 tokens
    │   ├─ 08_数据流分析: 600 tokens
    │   └─ 10_问题与修正: 600 tokens
    │
    ├─ 第2层: 公共知识库 (4000 tokens)
    │   ├─ 07_协议库/OneNet: 1500 tokens
    │   ├─ 08_架构库/调度系统: 1000 tokens
    │   ├─ 02_通信模块库/NBIot: 800 tokens
    │   └─ 06_算法库/校验: 700 tokens
    │
    └─ 第3层: 网上检索 (1500 tokens)
    ├─ 官方文档: 800 tokens
    ├─ GitHub示例: 400 tokens
    └─ 技术论坛: 300 tokens
    │
    ▼
[压缩策略] → 压缩后 (4000 tokens)
```

---

## Layer 1 Compression: Project KB

### 策略

项目专属问题最关注具体项目，优先保留：
1. 项目概述信息
2. 相关功能模块
3. 代码位置引用
4. 项目常见问题与调试切入点

### 压缩方法

```python
def compress_project_kb(results, max_tokens=1500):
    compressed = []

    # 1. 项目概述 (100 tokens)
    project_overview = extract_project_summary(results)
    compressed.append(project_overview)

    # 2. 相关功能模块 (800 tokens)
    relevant_modules = find_relevant_modules(results)
    for module in relevant_modules[:3]:  # 最多3个模块
        compressed.append(extract_module_summary(module))

    # 3. 代码位置引用 (400 tokens)
    code_locations = extract_code_locations(results)
    compressed.append(code_locations)

    # 4. 问题记录 (200 tokens)
    if has_relevant_issues(results):
        compressed.append(extract_relevant_issues(results))

    return compressed
```

### 压缩示例

**原始**（2500 tokens）：
```
项目3: NBIot报警主机

00_项目索引_地图.md
- 项目名: WG01 NBIot报警主机
- 版本: V3.6_260104
- 代码行数: ~25000行
- MCU: STM32F103C8T6

03_功能模块.md
- 功能1: NBIot模块 (hal_NBIot.c: ~1800行)
  - BC260Y_AT_Command_Table
  - NBIot_Status_Machine
  - NBIot_Rx_Handler
  - NBIot_Tx_Handler
- 功能2: 433M接收 (hal_rfd.c: ~350行)
  - EV1527_Decoder
  - RFDRcvMsg_Queue
- 功能3: 应用层 (app.c: ~2300行)
  - SystemMode_Handler
  - Alarm_Handler
  - Menu_Handler
... (更多内容)
```

**压缩后**（1500 tokens）：
```
## 项目: WG01 NBIot报警主机 (V3.6)

### 核心模块
- **NBIot模块**: `hal_NBIot.c` - BC260Y驱动，MQTT通信
- **433M接收**: `hal_rfd.c` - EV1527解码，无线报警
- **应用层**: `app.c` - 系统模式，报警处理，菜单

### 关键代码位置
- NBIot初始化: `hal_NBIot.c:67-75`
- OneNet连接: `hal_NBIot.c:241-300` (状态机)
- EV1527解码: `hal_rfd.c:解码函数`

### 已知问题
- OneNet连接超时: 见 `11_项目最常见的20个问题.md:问题1`
```

---

## Template-Aware Compression

For protocol, algorithm, timing, and framework questions in V4/V8 packs:

1. Keep concept identity, aliases, trigger chains, and debug entry points from `concept_index.jsonl` and `relation_index.jsonl` first.
2. If the concept hit carries `template_reference` or `template_doc_path`, keep only the matching template anchor title plus 3-6 checklist bullets from `08_ai_enrichment/core_concept_type_templates.md`.
3. Mark that template excerpt as `explanation scaffold only`, not as project evidence.
4. Reserve more token budget for project evidence from `fact_index.jsonl`, `human_docs`, and `source_snapshot` than for template text.
5. If token budget is tight, drop generic template prose before dropping project thresholds, formulas, timings, state transitions, or file anchors.

### Compression Heuristic

```python
def compress_template_scaffold(template_section, max_tokens=250):
    return {
        'type': 'template_scaffold',
        'anchor': template_section.anchor,
        'content': extract_checklist_bullets(template_section, limit=6),
        'evidence_role': 'explanation_only',
        'token_budget': min(max_tokens, 250),
    }
```

## Layer 2 Compression: Public KB

### 策略

通用技术问题和跨项目迁移需要：
1. 协议/算法的完整定义
2. 实现代码或伪代码
3. 使用示例
4. 迁移注意事项

### 压缩方法

```python
def compress_public_kb(results, max_tokens=2000):
    compressed = []

    # 1. 知识概述 (200 tokens)
    kb_overview = extract_kb_overview(results)
    compressed.append(kb_overview)

    # 2. 核心实现 (1000 tokens)
    core_implementation = extract_core_implementation(results)
    compressed.append(core_implementation)

    # 3. 使用示例 (600 tokens)
    examples = extract_usage_examples(results)
    compressed.append(examples)

    # 4. 迁移指南 (200 tokens)
    if is_migration_question:
        compressed.append(extract_migration_notes(results))

    return compressed
```

### 压缩示例

**原始**（4000 tokens）：
```
07_协议库/OneNet/OneNet_MQTT对接指南.md

## 协议概述
OneNet平台使用MQTT 3.1.1协议进行通信...

## 协议规范

### 基本参数
- 服务器: 183.230.40.96
- 端口: 1883
- MQTT版本: 3.1.1
- Client ID: {product_id}{device_id}
- Token: 64位十六进制

### CONNECT报文格式
| 字段 | 长度 | 说明 |
|-----|-------|------|
| 报文类型 | 1 | 0x10 |
| 长度 | 2 | 剩余长度 |
| 协议名 | 2 | "MQ" |
| 协议级别 | 1 | 4 |
| 标志 | 1 | 0x02 (用户名/密码) |
| 保活 | 2 | 0x3C 60秒 |
| Client ID | 变长 | 产品ID+设备ID |
| 用户名 | 变长 | 可选 |
| 密码 | 变长 | Token |

### 数据点格式
```json
{
  "id": 111,
  "dp": {
    "name": [{"v": "value"}]
  }
}
```

## 初始化序列

1. AT+QMTCFG="version",0,1
2. AT+QMTCFG="keepalive",0,60
3. AT+QMTOPEN=0,"183.230.40.96",1883
4. AT+QMTCONN=0,"client_id","password","token"
5. AT+QMTSUB=0,1,"$sys/product_id/device_id/dp/post/json"

... (更多内容，总共4000 tokens)
```

**压缩后**（2000 tokens）：
```
## OneNet MQTT协议 (V3.1.1)

### 核心参数
- 服务器: 183.230.40.96:1883
- Client ID格式: {product_id}{device_id}
- 保活: 60秒

### CONNECT流程
```c
1. AT+QMTCFG="version",0,1      // 配置MQTT版本
2. AT+QMTCFG="keepalive",0,60    // 配置保活
3. AT+QMTOPEN=0,"183.230.40.96",1883  // 打开连接
4. AT+QMTCONN=0,"{pid}{did}","pwd","token"  // 认证
5. AT+QMTSUB=0,1,"topic"             // 订阅主题
```

### 数据上报
```json
{"id":111,"dp":{"SystemMode":[{"v":"AwayArm"}]}}
```

### 迁移说明
- 协议100%可复用
- AT指令格式相同（BC260Y vs 其他NBIot模块）
- Client ID和Token需重新生成
```

---

## Layer 3 Compression: Web Retrieval

### 策略

网上检索是补充来源，只保留：
1. 官方文档的核心要点
2. API参考关键信息
3. 常见问题和解决方案

### 压缩方法

```python
def compress_web_results(results, max_tokens=500):
    compressed = []

    # 1. 官方文档摘要 (200 tokens)
    for doc in results.filter(r => r.source == 'official')[:2]:
        compressed.append(extract_official_summary(doc))

    # 2. API参考 (200 tokens)
    api_refs = extract_api_references(results)
    compressed.append(api_refs)

    # 3. 常见问题 (100 tokens)
    if has_common_questions(results):
        compressed.append(extract_common_questions(results))

    return compressed
```

### 压缩示例

**原始**（1500 tokens）：
```
官方文档搜索结果：

STM32F1xx HAL库用户手册 (UM1850)
文档链接: https://www.st.com/resource/en/user_manual/um1850-stm32f1x-standard-peripheral-library.html

相关章节：
1. GPIO外设描述
   - GPIO简介
   - GPIO主要特性
   - GPIO寄存器描述
   - HAL_GPIO库函数
2. GPIO配置示例
   - GPIO_Init
   - GPIO_ReadPin
   - GPIO_WritePin
   - GPIO_SetBits
   - GPIO_ResetBits
3. 中断和事件
   - EXTI配置
   - GPIO中断处理
   - 事件线配置

AT32F421 HAL库快速参考
文档链接: https://www.artertek.com/...

API对比表:
| 功能 | STM32 HAL | AT32 HAL | 迁移说明 |
|-----|-----------|---------|---------|
| GPIO初始化 | HAL_GPIO_Init | gpio_init() | API改名 |
| GPIO读 | HAL_GPIO_ReadPin | gpio_input_data_read() | 新API |
| GPIO写 | HAL_GPIO_WritePin | gpio_output_data_set() | 新API |
... (更多对比)
```

**压缩后**（500 tokens）：
```
## 官方参考

**STM32F1x HAL**:
- `HAL_GPIO_Init()` → GPIO初始化
- `HAL_GPIO_ReadPin()` → 读取引脚
- `HAL_GPIO_WritePin()` → 设置引脚

**AT32F421 HAL**:
- `gpio_init()` → GPIO初始化
- `gpio_input_data_read()` → 读取引脚
- `gpio_output_data_set()` → 设置引脚

### 迁移关键点
- API名称变化（需查找替换）
- 寄存器定义可能不同
- 中断处理方式可能不同
```

---

## Progressive Disclosure

```python
class ContextManager:
    """上下文管理器，实现渐进式加载"""

    def __init__(self, max_tokens=4000):
        self.max_tokens = max_tokens
        self.current_tokens = 0

    def add_content(self, content, priority='medium'):
        """添加内容，动态调整详细程度"""

        estimated_tokens = estimate_tokens(content)
        remaining = self.max_tokens - self.current_tokens

        if estimated_tokens <= remaining:
            # 容量充足，添加完整内容
            return {'include': True, 'content': content}
        else:
            # 容量不足，提取关键信息
            if priority == 'high':
                return extract_key_points(content)
            else:
                return extract_summary(content)
```

---

## Token Estimation

| 内容类型 | 估算方法 | 示例 |
|---------|---------|------|
| 文本 | words × 0.75 | 1000词 ≈ 750 tokens |
| 代码 | lines × 4 | 100行代码 ≈ 400 tokens |
| 表格 | cells × 1.5 | 50个单元格 ≈ 75 tokens |
| Markdown标题 | 1 token × 级别 | 标题1级 ≈ 10 tokens |
| 代码块 | lines × 5 | 10行代码 ≈ 50 tokens |

---

## Compression Quality Metrics

| 指标 | 目标 | 说明 |
|-----|------|------|
| 信息保留率 | >80% | 压缩后保留的信息比例 |
| 相关性保持 | >90% | 压缩后与问题的相关性 |
| 可读性 | 高 | 压缩后内容仍易于理解 |
| 引用完整性 | 100% | 所有引用必须包含位置 |

