---
name: mcu-project-organizer-v13
description: MCU 项目知识库构建 Skill V13 — 直接读源码+双模式+12文档+SUMMARY
---

# MCU 项目知识库构建 Skill V13

## 快速调用指南

### 全量生成（第一次整理项目）
1. 双击 bootstrap.cmd 提取项目上下文
2. 说："请读取 SKILL.md，对 [路径] 执行完整知识库构建流程"

### 单独补厚某个文档
说："请读取 sub-skills/[子skill文件名]，
     补厚 [知识库路径] 的 [文档名]"

子skill文件 对应的 输出文档：
  01_doc_overview.md    → 00_阅读指南 + 01_项目介绍
  02_doc_hardware.md    → 02_硬件配置
  03_doc_architecture.md→ 03_系统架构
  04_doc_modules.md     → 04_功能模块
  05_doc_protocols.md   → 05_通信协议
  06_doc_params.md      → 06_关键参数表
  07_doc_issues.md      → 07_已知问题与建议
  08_doc_dataflow.md    → 08_数据流与控制流
  10_doc_newcomer.md    → 09_项目结构总览
  11_doc_semantics.md   → 10_代码语义化
  12_doc_faq.md         → 11_常见问题清单
  13_doc_summary.md     → SUMMARY.md
  14_doc_experience.md  → 12_历史经验库（经验层：聊天记录/口述/Word文档）
  15_verification_package.md → 验收包.md（交付前质量验证，客户填写）

### 重跑分析引擎（源码有大更新时）
说："请读取 sub-skills/00_analysis_engine.md，
     重新分析 [知识库路径]，刷新 _analysis/ 索引"

---

## 架构升级: V12 → V13

V13 基于《MCU-Skill优化指导书-v2》进行核心架构修复和功能扩展。

**核心改进**:
- **根本修复**: 子skill从依赖 `_analysis/`（薄摘要）改为直接读源码，`_analysis/` 仅做导航索引
- **双模式**: 所有子skill同时支持"流水线模式"和"单独补厚模式"
- **新增铁律**: 铁律8（必须直接读源码）+ 铁律9（补厚不覆盖）
- **文档扩展**: 从9个文档扩展为12+1个（新增项目总览、代码语义化、FAQ、SUMMARY）
- **质量保证**: 验证清单新增F/G/H三组检查项

```
❌ v12做法：_analysis/（薄摘要）→ 直接写入文档
✅ v13做法：_analysis/（导航索引）→ 源码（完整数据）→ 写入文档
```

## 目标

从任意 MCU 项目（Keil/IAR）自动提取编译上下文，通过 AI 调用链驱动分析，生成**超越开发者认知深度**的项目知识库文档。

### 双重目标
| 读者 | 要求 |
|---|---|
| **人类（企业/工程师）** | 第一眼惊艳，比原开发者更懂项目——挖个底朝天 |
| **AI（QA Assistant）** | 数值全解析、链路完整、无歧义，可直接引用回答问题 |

## 整体架构

```
第 1 层: 确定性提取 (bootstrap.cmd 一键执行)
  ├─ _v10_context/project_context.json   (宏定义/源文件/include路径)
  ├─ _v10_snapshot/                      (活跃源码+头文件副本)
  └─ _v10_context/call_graph_hint.json   (函数定义/调用关系)

第 2 层: AI 深度分析 (子skill 0: 分析引擎)
  └─ _analysis/                          (13个结构化中间产物 — 导航索引)

第 3 层: AI 文档生成 (子skill 1-8 + 10-12: 各文档生成器)
  └─ 知识库文档 12+1 个 (00-08 + 09-11 + SUMMARY)

第 4 层: AI 验证修正 (子skill 9: 验证器)
  └─ 验证报告 + 自动修正

第 5 层: QA 问答 (mcu-qa-assistant)
  └─ 基于知识库 + 源码回查
```

## 文件结构

```
mcu-project-organizer-v13/
├── SKILL.md                    ← 你正在读的文件 (编排器)
├── bootstrap.cmd               ← 第1层: 确定性提取
├── scripts/                    ← 提取脚本
│   ├── 00_common.ps1
│   ├── 01_extract_project_context.ps1
│   ├── 02_export_source_snapshot.ps1
│   ├── 03_build_call_graph_hint.ps1
│   └── verify_output.py
│
├── sub-skills/                 ← 子skill集
│   ├── 00_analysis_engine.md   ← 源码深度分析引擎
│   ├── 01_doc_overview.md      ← 00_阅读指南 + 01_项目介绍
│   ├── 02_doc_hardware.md      ← 02_硬件配置
│   ├── 03_doc_architecture.md  ← 03_系统架构
│   ├── 04_doc_modules.md       ← 04_功能模块
│   ├── 05_doc_protocols.md     ← 05_通信协议
│   ├── 06_doc_params.md        ← 06_关键参数表
│   ├── 07_doc_issues.md        ← 07_已知问题与建议
│   ├── 08_doc_dataflow.md      ← 08_数据流与控制流
│   ├── 09_verification.md      ← 验证与修正
│   ├── 10_doc_newcomer.md      ← 09_项目结构总览（新增）
│   ├── 11_doc_semantics.md     ← 10_代码语义化（新增）
│   ├── 12_doc_faq.md           ← 11_常见问题清单（新增）
│   └── 13_doc_summary.md       ← SUMMARY.md（新增）
│
└── shared/                     ← 共享规则 (子skill按需引用)
    ├── iron_rules.md           ← 铁律 0-9
    ├── format_spec.md          ← 排版规范
    └── quality_checklist.md    ← 质量检查清单
```

## 第 1 层: 使用 bootstrap.cmd

与 V12 完全相同:
- 双击 `bootstrap.cmd`，输入项目路径和输出目录即可
- 或在命令行: `bootstrap.cmd "E:\path\to\project" "E:\path\to\output"`

## 第 2-4 层: AI 分析执行指令

### 前置条件
确认第 1 层已执行完成:
- `_v10_context/project_context.json` 存在
- `_v10_snapshot/` 目录存在并包含源码
- `_v10_context/call_graph_hint.json` 存在

### 执行顺序

> ⚠️ **必须按以下顺序执行子skill。每个子skill执行前，先读取对应的子skill文件。**

---

#### 阶段 1: 深度分析

**读取并执行**: `sub-skills/00_analysis_engine.md`

**输入**: 第1层提取结果 (`project_context.json` + `source_snapshot/` + `call_graph_hint.json`)

**产出**: `_analysis/` 目录下 13 个中间分析文件:

| 文件 | 内容 |
|------|------|
| `project_overview.md` | 芯片型号、代码统计、目录结构 |
| `clock_tree.md` | 时钟树完整分析 |
| `gpio_and_pins.md` | GPIO引脚、重映射 |
| `peripheral_config.md` | 外设详细配置 |
| `nvic_priorities.md` | NVIC优先级表 |
| `system_init_and_tasks.md` | 启动顺序、任务列表 |
| `memory_layout.md` | Flash/RAM/Stack/Heap |
| `module_analysis.md` | 各模块详细分析 |
| `protocol_analysis.md` | 通信协议分析 |
| `data_flow.md` | 数据流链路 |
| `data_structures.md` | 核心数据结构 |
| `hardcoded_params.md` | 硬编码参数 |
| `issues_and_risks.md` | BUG、冲突、风险 |

**检查点**: 确认 `_analysis/` 下所有 13 个文件已创建，再进入下一阶段。

---

#### 阶段 2: 文档生成

按顺序执行以下子skill。每个子skill使用 `_analysis/` 做**导航索引**，然后**直接读源码**提取完整数据。

| 执行顺序 | 子Skill | 读取的子skill文件 | 产出文档 | 模式支持 |
|---------|---------|------------------|---------|---------| 
| 2.1 | 概览 | `sub-skills/01_doc_overview.md` | `00_阅读指南.md` + `01_项目介绍.md` | 流水线+单独 |
| 2.2 | 硬件 | `sub-skills/02_doc_hardware.md` | `02_硬件配置.md` | 流水线+单独 |
| 2.3 | 架构 | `sub-skills/03_doc_architecture.md` | `03_系统架构.md` | 流水线+单独 |
| 2.4 | 模块 | `sub-skills/04_doc_modules.md` | `04_功能模块.md` | 流水线+单独 |
| 2.5 | 协议 | `sub-skills/05_doc_protocols.md` | `05_通信协议.md` | 流水线+单独 |
| 2.6 | 参数 | `sub-skills/06_doc_params.md` | `06_关键参数表.md` | 流水线+单独 |
| 2.7 | 问题 | `sub-skills/07_doc_issues.md` | `07_已知问题与建议.md` | 流水线+单独 |
| 2.8 | 数据流 | `sub-skills/08_doc_dataflow.md` | `08_数据流与控制流.md` | 流水线+单独 |
| 2.9 | 新人总览 | `sub-skills/10_doc_newcomer.md` | `09_项目结构总览.md` | 流水线+单独 |
| 2.10 | 代码语义 | `sub-skills/11_doc_semantics.md` | `10_代码语义化.md` | 流水线+单独 |
| 2.11 | 常见问题 | `sub-skills/12_doc_faq.md` | `11_常见问题清单.md` | 流水线+单独 |
| 追加 | 历史经验 | `sub-skills/14_doc_experience.md` | `12_历史经验库.md` | **仅单独**（用户主动投喂）|

**每个子skill执行时**:
1. 先读取对应的 `sub-skills/XX_xxx.md` 文件
2. 再读取文件中指定的 `shared/` 共享规则（铁律、排版规范）
3. 读取 `_analysis/` 中指定的中间分析文件 **作为导航索引**
4. **直接读 `_v10_snapshot/` 源码提取完整数据**（铁律8）
5. 输出最终文档到知识库目录

**检查点**: 确认 12 个文档全部生成，再进入验证阶段。

---

#### 阶段 3: 验证与修正

**读取并执行**: `sub-skills/09_verification.md`

**操作**:
1. 运行 `scripts/verify_output.py`
2. 执行完整性检查（含新增文档）
3. 执行正确性回查验证
4. 修正发现的问题
5. 输出验证报告

**检查点**: `verify_output.py` 返回通过，或所有失败项已修正。

---

#### 阶段 4: 汇总

**读取并执行**: `sub-skills/13_doc_summary.md`

**操作**:
1. 读取所有已生成的知识库文档
2. 汇总生成 `SUMMARY.md`（一页纸总结）

**检查点**: `SUMMARY.md` 已创建，包含架构图和风险列表。

---

#### 阶段 5: 生成验收包（交付前必做）

> ⚠️ **此步骤不可跳过**。验收包是交付给客户的质量证明，也是你自己的质量把关工具。

**读取并执行**: `sub-skills/15_verification_package.md`

**操作**:
1. 读取 `shared/anchor-questions.md`（20道锚点题）
2. 从知识库文档中逐题提取答案（带证据链）
3. 提取约50条核心事实清单
4. 提取5个关键流程
5. 从 `11_常见问题清单.md` 生成20道盲测题
6. 输出 `验收包.md`

**检查点**:
- `验收包.md` 已创建
- Part 1 锚点自测初步评级 **不低于 ⚠️局部缺失**
- 如果评级为 ❌不达标 → 返回阶段2补厚对应文档，再重新执行阶段3-5

---

#### 交付清单

全部阶段完成后，向客户交付以下文件：

```
✅ 知识库文档（00-11 共12个 + SUMMARY.md）
✅ 验收包.md（客户填写，2-4小时）
✅ 12_历史经验库.md（如已有经验投喂）
```

并附说明：
> 验收通过标准：Part 1 锚点自测 ≥ 18题，Part 4 盲测得分 ≥ 75%。
> 发现错误请直接在验收包里备注，我将逐条更新知识库。

---

## 节点依赖关系图（H6修复）

> 明确哪些步骤必须按序，哪些可选，哪些可并行，避免不同用户因顺序错误导致质量差异。

```
[必须] 阶段0: bootstrap.cmd
         ↓ 必须完成，否则后续无法执行
[必须] 阶段1: 00_analysis_engine
         ↓ 必须完成
[必须] 阶段2: 01-12 子skill（顺序固定，不可跳过）
         │
         ├─→ [可选] 14_doc_experience（经验层投喂）
         │       依赖：04_功能模块 已生成（用于关联检查）
         │       时机：可在阶段2任意时刻插入，也可交付后追加
         │       不依赖：其他子skill，可独立运行
         │
         ↓ 阶段2全部完成后
[必须] 阶段3: 09_verification（验证修正）
         ↓
[必须] 阶段4: 13_doc_summary（SUMMARY.md）
         ↓ 自动提示下一步
[必须] 阶段5: 15_verification_package（验收包，交付前）
         ↓
       交付客户
```

**14_doc_experience 特别说明**：
- 首次交付前：如有历史经验可投喂，在阶段3之前完成，让验证阶段能检测到经验库
- 交付后追加：客户使用过程中产生新经验，随时可追加，无需重跑后续阶段
- 不影响验收包生成：验收包是否包含历史经验库条目，取决于生成时 12_历史经验库.md 是否存在

**15_verification_package 特别说明**：
- 前置条件：01/02/03/05/06/07/11 必须存在（否则验收包内容严重缺失，停止执行）
- 降级处理：若 08/09/10 缺失，验收包仍可生成，但 Part 3 对应流程章节留空并标注原因
- 不可并行：必须在阶段4（SUMMARY.md）完成后运行，因为 Part 4 盲测题从 11_FAQ 提取

---

## 共享规则说明

| 文件 | 内容 | 被谁引用 |
|------|------|---------| 
| `shared/iron_rules.md` | 铁律 0-9 (代码即事实、宏解析、芯片精确、直接读源码、补厚不覆盖...) | 所有子skill |
| `shared/format_spec.md` | 表格格式、Mermaid类型、标题层级 | 文档生成子skill 1-8, 10-13 |
| `shared/quality_checklist.md` | 质量要求 + 检查项清单（含新增F/G/H组） | 验证子skill 9 |

**关键**: 每个子skill只引用自己需要的共享文件，不全部加载。

---

## 中间产物数据流

```
                    ┌──────────────────────┐
                    │ 00_analysis_engine   │
                    │   (读全部源码)        │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    _analysis/ 目录    │
                    │  (13个导航索引文件)    │
                    └──────────┬───────────┘
            ┌──────────┬──────┼──────┬──────────┐
            ▼          ▼      ▼      ▼          ▼
      ┌──────────┐ ┌──────┐ ┌───┐ ┌───┐ ┌──────────┐
      │01_overview│ │02_hw │ │...│ │...│ │12_faq    │
      │          │ │      │ │   │ │   │ │          │
      │ ↓读源码  │ │↓读源码│ │   │ │   │ │↓读已有文档│
      └─────┬────┘ └──┬───┘ └─┬─┘ └─┬─┘ └─────┬────┘
            │         │       │     │          │
            ▼         ▼       ▼     ▼          ▼
      ┌─────────────────────────────────────────────┐
      │        12+1个知识库文档 (00-11 + SUMMARY)     │
      └──────────────────┬──────────────────────────┘
                         │
              ┌──────────▼───────────┐
              │  09_verification     │
              │  (验证 + 修正)        │
              └──────────┬───────────┘
                         │
              ┌──────────▼───────────┐
              │  13_doc_summary      │
              │  (SUMMARY.md 汇总)   │
              └──────────────────────┘
```

## 单文档重跑/补厚支持

V13 架构的关键优势：

1. **重跑**: 如果某个文档质量不满意，可以**只重跑对应的子skill**
2. **补厚**: 如果文档已存在但不够完整，子skill会**只补充缺失内容**（铁律9）

例如，补厚 05_通信协议:
1. 说："请读取 sub-skills/05_doc_protocols.md，补厚知识库里的通信协议文档"
2. 子skill读取现有 `05_通信协议.md`，发现缺少完整AT指令列表
3. 直接读源码补全，追加到文档末尾
4. 报告：已补充AT指令表（+8条）

前提: `_analysis/` 中的中间产物仍然有效。
