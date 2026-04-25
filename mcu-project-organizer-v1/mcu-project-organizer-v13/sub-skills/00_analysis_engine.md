# 子Skill 0: 源码深度分析引擎

> **职责**: 读取第1层确定性提取的结果，对全部源码进行深度分析，输出结构化的中间分析文件。
> **本子skill不生成任何最终文档**，只输出 `_analysis/` 目录下的结构化数据。

---

## 前置条件

确认以下文件/目录存在:
- `_v10_context/project_context.json` — 宏定义和源文件列表
- `_v10_snapshot/sources/` — 源码快照
- `_v10_snapshot/headers/` — 头文件快照
- `_v10_context/call_graph_hint.json` — 调用关系提示

## 必须遵守的共享规则

**在开始分析前，先读取 `shared/iron_rules.md`**，整个分析过程必须严格遵守铁律 0-9。

---

## 分析步骤

### 步骤 1: 读取编译上下文

1. 读 `project_context.json`，记录:
   - `device` 字段 → **这就是精确芯片型号**（如 `STM32F103C8`，由脚本从Keil工程文件确定性提取）
   - `flash_start` / `flash_size` → Flash 起始地址和大小
   - `ram_start` / `ram_size` → RAM 起始地址和大小
   - `active_macros` 列表 (条件编译判断用)
   - `business_sources` 列表 (待分析的文件清单)
   - `target_name`
2. 读 `call_graph_hint.json`，了解函数定义位置和调用关系
3. **芯片型号直接使用 `device` 字段的值**，如 `STM32F103C8` → 完整型号为 `STM32F103C8T6`（T6为封装后缀，代码中通常不含）。写入文档时加 `[需硬件确认封装后缀]` 注释即可

**输出**: `_analysis/project_overview.md`

```markdown
## 芯片型号
[精确型号] (来源: [确认方式])

## 编译上下文
- 有效宏: [列表]
- 业务源文件数: X
- 第三方源文件数: Y
- 头文件数: Z
- Target: [名称]

## 代码统计
| 指标 | 数据 |
|------|------|
| 业务源文件 | X个 |
| 有效代码行数 | ~Y行 |
| 函数数量 | Z个 |
| 全局变量数 | W个 |

## 源码目录结构
[带文件大小和职责标注的目录树]
```

### 步骤 2: 时钟树分析 ← 最优先

> ⚠️ 这是最容易出错的地方。注释中的时钟频率经常是错误的！

1. **找到系统时钟源头**:
   - STM32: 在 `system_stm32f10x.c` 中搜索 `#define SYSCLK_FREQ_` 开头的宏，确定实际编译的频率
   - 其他芯片: 找到 `SystemCoreClockUpdate()` 或等效函数，追踪 PLL 配置
2. **追踪总线时钟分频**:
   - AHB 分频 (HCLK) → 决定 DMA/GPIO 时钟
   - APB1 分频 (PCLK1) → 决定 TIM2/3/4/USART2/3/I2C/SPI2 等低速外设时钟
   - APB2 分频 (PCLK2) → 决定 TIM1/USART1/SPI1/ADC 等高速外设时钟
3. **验证定时器实际频率**: 用 `APBx时钟 x 倍频系数` 计算，而非信任注释中的频率值
4. **验证串口波特率**: 反推 `USART_BRR` 寄存器值是否与声称的波特率一致

**输出**: `_analysis/clock_tree.md`

```markdown
## 时钟源
- HSE: [频率] [来源]
- HSI: [频率]
- PLL配置: [倍频/分频参数] (来源: [文件:行号])

## 时钟树
- SYSCLK: [频率] (来源: [宏/寄存器配置])
- AHB (HCLK): [频率] (分频系数: [X])
- APB1 (PCLK1): [频率] (分频系数: [X])
- APB2 (PCLK2): [频率] (分频系数: [X])
- APB1 定时器时钟: [频率] (倍频: [X])
- APB2 定时器时钟: [频率] (倍频: [X])

## 注释vs代码冲突
[如果发现注释频率与代码不一致，在此记录]
```

### 步骤 3: 从 main() 自顶向下追踪

1. 从 `main()` 函数开始，记录初始化调用顺序
2. 找到所有 **任务入口函数**（如 OS 任务、裸机主循环中的调用）
3. 对每个任务入口，**递归追踪它调用的每一个函数**:
   - 读该函数的源码
   - 记录它操作了哪些外设/GPIO/寄存器
   - 记录关键参数和阈值
   - 如果该函数调用了其他函数，继续追踪
4. 对每个 **中断服务程序 (ISR)**，单独追踪其回调链

**输出**: `_analysis/system_init_and_tasks.md`

```markdown
## 启动顺序
1. [SystemInit()] → 时钟配置
2. [xxx_Init()] → ...
3. ...

## 调度器类型
[RTOS名称/协作式/裸机] (来源: [证据])

## 任务列表
| 任务名 | 入口函数 | 周期 | 优先级 | 来源 |
|--------|---------|------|--------|------|
| ... | ... | ... | ... | [文件:行号] |

## 中断列表
| ISR名称 | 触发源 | 回调函数 | 来源 |
|---------|--------|---------|------|
| ... | ... | ... | [文件:行号] |
```

### 步骤 3.5: 外设引脚强制提取

> ⚠️ 这是引脚遗漏的最大来源。以下步骤对每个业务源文件必须执行，不能跳过。

**对 project_context.json 中的每个 business_source `.c` 文件:**

1. **读取文件头部50行**: 提取所有 `#define xxx_PORT`/`#define xxx_PIN` 宏定义
2. **搜索 GPIO_Init()**: 搜索 `GPIO_Init(` 关键词，记录每个GPIO配置
3. **搜索外设寄存器直接访问**: 搜索 `SPI1->`, `I2C1->`, `TIM3->`, `USART1->` 等模式
4. **搜索 RCC 时钟使能**: 搜索 `RCC_APB1PeriphClockCmd`/`RCC_APB2PeriphClockCmd`

**大文件分段阅读策略**:

| 文件类型 | 特征 | 关键信息位置 | 阅读策略 |
|----------|------|------------|----------|
| 显示驱动(OLED/LCD) | 80%+是字库`{0xXX,...}` | 前30行(#define引脚) + Init函数 | 读前50行 + 搜索Init/GPIO_Init |
| 通信协议栈(AT指令) | 大量AT命令字符串和switch/case | 前100行(#define) + 状态机 | 读前100行 + 搜索case枚举 |
| 应用层(menu/UI) | 大量字符串和结构体初始化 | Init函数 + 回调注册 | 读Init + 回调函数 |

**输出**: `_analysis/gpio_and_pins.md`

```markdown
## GPIO 引脚完整列表

### 来自 #define 宏定义
| 宏名 | 端口 | 引脚 | 来源 |
|------|------|------|------|
| LED1_PIN | GPIOC | GPIO_Pin_14 | hal_led.h:5 |
| ... |

### 来自 GPIO_Init() 直接配置
| 端口 | 引脚 | 模式 | 速率 | 功能 | 来源 |
|------|------|------|------|------|------|
| ... |

### RCC 时钟使能记录
| 调用 | 使能的外设 | 来源 |
|------|-----------|------|
| RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE) | GPIOA | xxx.c:30 |
| ... |
```

### 步骤 4: GPIO 重映射检查

- 搜索所有 `GPIO_PinRemapConfig` / `GPIO_AF` 调用
- 如果有重映射，引脚分配以**重映射后的引脚**为准
- 记录使用的重映射类型 (部分重映射/完全重映射)
- 对所有 `GPIO_Remap_SWJ_*` 调用，明确记录释放和保留的引脚

**追加到**: `_analysis/gpio_and_pins.md`

```markdown
## AFIO 重映射
| 重映射调用 | 类型 | 释放的引脚 | 占用/保留的引脚 | 来源 |
|-----------|------|-----------|--------------|------|
| ... |
```

### 步骤 4.5: 外设枚举清单

对以下外设类型逐一确认使用情况，在全部源码中搜索对应关键词:

| 外设类型 | 搜索关键词 | 状态 |
|----------|-----------|------|
| USART/UART | `USART_Init`, `USART1`, `USART2`, `USART3` | 已用/未用 |
| SPI | `SPI_Init`, `SPI1->`, `SPI2->` | 已用/未用 |
| I2C (硬件) | `I2C_Init`, `I2C1->`, `I2C2->` | 已用/未用 |
| I2C (软件) | 手动GPIO模拟SCL/SDA时序 | 已用/未用 |
| TIMx | `TIM_TimeBaseInit`, `TIM2`, `TIM3`, `TIM4` | 已用/未用 |
| ADC | `ADC_Init`, `ADC1->` | 已用/未用 |
| DMA | `DMA_Init`, `DMA1_Channel` | 已用/未用 |
| CAN | `CAN_Init` | 已用/未用 |
| IWDG/WWDG | `IWDG_`, `WWDG_` | 已用/未用 |
| AFIO | `GPIO_PinRemapConfig`, `GPIO_AF` | 已用/未用 |
| EXTI | `EXTI_Init` | 已用/未用 |
| RTC | `RTC_Init` | 已用/未用 |

**输出**: `_analysis/peripheral_config.md`

```markdown
## 外设使用总表
| 外设 | 状态 | 引脚 | 关键参数 | 功能模块 | 来源 |
|------|------|------|---------|---------|------|
| USART1 | 已用 | PA9(TX)/PA10(RX) | 115200,8N1 | 调试串口 | hal_usart.c:25 |
| ... |

## 各外设详细配置

### USART1
- 波特率: 115200 (来源: xxx.c:行号)
- 收发方式: 中断/DMA/轮询
- 连接: [外部器件]
- NVIC配置: 抢占优先级X, 子优先级Y (来源: xxx.c:行号)
...

### [重复每个已用外设]
```

### 步骤 5: 条件编译处理

- 遇到 `#ifdef`, `#if defined()` 等条件编译时
- 查 `project_context.json` 中的 `active_macros` 列表
- **只分析当前 Target 有效的分支**，忽略无效分支
- 记录所有受条件编译影响的功能

### 步骤 6: 注释 vs 代码冲突检测

> ⚠️ 嵌入式项目中注释过时/错误的概率极高(超过30%)！

**规则**: 当注释中的数值与代码计算结果不一致时:
1. 以**代码计算结果**为准
2. 记录到冲突列表中

**输出**: `_analysis/issues_and_risks.md`

```markdown
## 注释vs代码冲突
| 文件:行号 | 注释描述 | 实际代码 | 严重度 |
|----------|---------|---------|--------|
| xxx.c:45 | //48MHz | 宏定义 72MHz | P1 |
| ... |

## 潜在BUG
| 文件:行号 | 现象 | 影响 | 严重度 |
|----------|------|------|--------|
| ... |

## 竞态条件风险
| 变量名 | ISR中访问 | 主循环中访问 | 是否有临界区保护 | 来源 |
|--------|----------|------------|----------------|------|
| ... |

## 设计风险
| 描述 | 影响 | 严重度 | 来源 |
|------|------|--------|------|
| ... |

## 改进建议
| 描述 | 收益 | 优先级 |
|------|------|--------|
| ... |
```

### 步骤 7: NVIC 优先级分析

**输出**: `_analysis/nvic_priorities.md`

```markdown
## 优先级分组
- Group设置: [X] (来源: [文件:行号])
- 抢占优先级位数: [X]
- 子优先级位数: [X]

## 中断优先级表
| 中断源 | 设置抢占优先级 | 设置子优先级 | 实际生效值 | 来源 |
|--------|-------------|------------|-----------|------|
| ... |

## 优先级冲突分析
[是否存在优先级截断或意外的抢占关系]
```

### 步骤 8: 内存布局分析

- 查找 Keil `.sct` 散列文件 或 GCC `.ld` 链接脚本
- 如果不存在，从启动文件 `startup_*.s` 中提取 Stack_Size / Heap_Size
- 从 Keil 工程文件的 Target 配置中提取 Flash/RAM 起始地址和大小

**输出**: `_analysis/memory_layout.md`

```markdown
## Flash/RAM 布局
| 区域 | 起始地址 | 大小 | 用途 | 来源 |
|------|---------|------|------|------|
| Flash | 0x08000000 | 256KB | 代码 | ... |
| RAM | 0x20000000 | 64KB | 数据 | ... |

## Bootloader地址空间 (如有)
| 区域 | 起始地址 | 大小 | 来源 |
|------|---------|------|------|
| ... |

## Stack/Heap
| 参数 | 大小 | 来源 |
|------|------|------|
| Stack_Size | 0x400 (1KB) | startup_xxx.s:行号 |
| Heap_Size | 0x200 (512B) | startup_xxx.s:行号 |

## RAM占用估算
| 模块 | 全局/静态变量 | 估算大小 | 来源 |
|------|------------|---------|------|
| ... |
| **合计** | | **XX KB / YY KB (ZZ%)** | |

## 栈深度估算
- 最深调用链: main → xxx → yyy → zzz
- 估算最坏情况栈使用量: XX bytes
- vs Stack_Size (YY bytes): [安全/危险]
```

### 步骤 9: 模块分析 ← 函数级全覆盖

> ⚠️ **这是V12.1的核心改进。之前只提取"对外API"导致函数覆盖率不到25%。**
> **现在要求：call_graph_hint.json 中每个业务文件的每个函数定义，都必须在本文件中有记录。**

#### 9.1 从 call_graph_hint.json 提取函数清单

读取 `_v10_context/call_graph_hint.json` 中的 `function_defs` 字段。
对每个业务 `.c` 文件，获取其完整的函数定义列表（函数名 + 行号）。

**排除以下类型的函数（不需要记录）：**
- `stm32f10x_it.c` 中的标准异常处理器（NMI_Handler, HardFault_Handler, MemManage_Handler, BusFault_Handler, UsageFault_Handler, SVC_Handler, DebugMon_Handler, PendSV_Handler）
- `system_stm32f10x.c` 中的系统函数（SystemInit, SetSysClock, SetSysClockTo24/36/48/56/72, SetSysClockToHSE, SystemCoreClockUpdate, SystemInit_ExtMemCtl）

#### 9.2 逐文件分析并区分函数类型

对每个业务模块，**读取对应源码文件**，将函数分为两类：

**对外API（Public）**：在 `.h` 头文件中声明、被其他模块调用的函数
- 典型命名：`xxx_Init()`, `xxx_Proc()`, `xxx_GetXxx()`, `xxx_SetXxx()`, `xxxRegister()`

**内部函数（Private）**：仅在本 `.c` 文件内使用的函数
- 典型命名：`xxxConfig()`, `xxxHandle()`, `xxxDrive()`, `static` 函数
- 包括：ISR处理函数、定时器回调、内部状态机处理、GPIO底层操作等

#### 9.3 对大模块（app.c等）必须细分

对于超过500行的大文件（如 app.c），需要按功能子分区列出：
- 系统模式处理函数（S_ENArmModeProc, S_DisArmModeProc 等）
- 菜单回调函数（stgMenu_xxx, gnlMenu_xxx 等）
- 事件处理回调（KeyEventHandle, RfdRcvHandle, ServerEventHandle）
- 工具函数（HexToAscii, ScreenControl 等）

**输出**: `_analysis/module_analysis.md`

```markdown
## 模块列表

### [模块名] (xxx.c + xxx.h)
- **职责**: [一句话描述]
- **代码行数**: ~X行
- **初始化函数**: xxx_Init() (xxx.c:行号)
- **主循环函数**: xxx_Process() (xxx.c:行号)

#### 对外 API (Public)
| 函数名 | 参数 | 返回值 | 功能 | 行号 |
|--------|------|--------|------|------|
| xxx_Init | void | void | 初始化 | xxx.c:行号 |
| ... |

#### 内部函数 (Private)
| 函数名 | 调用者/触发方式 | 功能概述 | 行号 |
|--------|---------------|---------|------|
| xxxConfig | xxx_Init调用 | GPIO/外设配置 | xxx.c:行号 |
| xxxHandle | 定时器回调 | 周期性处理 | xxx.c:行号 |
| xxxDrive | xxxHandle调用 | 底层硬件操作 | xxx.c:行号 |
| ... |

- **依赖**: [其他模块名列表]
- **被依赖**: [其他模块名列表]
- **关键状态机/算法**: [描述]
```

#### 9.4 函数覆盖率自检

分析完成后，逐一核对 `call_graph_hint.json` 中的 `function_defs`：
- 该文件中每个函数名是否都出现在 `module_analysis.md` 中？
- 遗漏的函数 → 回到源码读取该函数并补充
- **目标覆盖率: 100% 业务函数**（排除步骤9.1中列出的系统函数）

### 步骤 10: 通信协议分析

对每种通信协议:
- 帧结构
- 命令字/端点号（带数值）
- 状态机转换
- 超时/重试参数
- 收发处理链

**输出**: `_analysis/protocol_analysis.md`

```markdown
## 协议列表

### [协议名称] (通过 [USARTx/SPIx])
- **类型**: 标准/自定义
- **帧结构**:
  | 偏移 | 长度 | 名称 | 说明 |
  |------|------|------|------|
  | 0 | 1 | 帧头 | 0xAA |
  | ... |
- **命令字表**:
  | 命令名 | 数值 | 方向 | 功能 | 来源 |
  |--------|------|------|------|------|
  | ... |
- **状态机**:
  | 当前状态 | 事件 | 下一状态 | 动作 | 来源 |
  |---------|------|---------|------|------|
  | ... |
- **超时/重试**: [参数描述]
- **收发链路**: ISR → 缓冲区 → 解析函数 → 业务回调
```

### 步骤 11: 数据流分析

追踪 2-3条核心业务场景的端到端数据链路。

**输出**: `_analysis/data_flow.md`

```markdown
## 队列/缓冲区清单
| 名称 | 类型 | 大小 | 生产者 | 消费者 | 来源 |
|------|------|------|--------|--------|------|
| ... |

## 核心数据链路

### 链路1: [场景名称]
1. **[节点名]** (xxx.c:行号)
   - 输入: [数据格式]
   - 处理: [核心逻辑]
   - 输出: [传递方式] → 下一节点
2. **[节点名]** (xxx.c:行号)
   ...
```

### 步骤 12: 核心数据结构提取

**输出**: `_analysis/data_structures.md`

```markdown
## 核心数据结构

### [结构体名] (定义于 xxx.h:行号)
```c
typedef struct {
    uint8_t field1;   // [字段含义]
    uint16_t field2;  // [字段含义]
    ...
} StructName;
```
- **用途**: [一句话说明]
- **大小**: XX bytes
- **使用位置**: [哪些模块使用]

### [枚举名] (定义于 xxx.h:行号)
| 枚举值 | 数值 | 含义 |
|--------|------|------|
| ... |
```

### 步骤 13: 硬编码参数提取

**输出**: `_analysis/hardcoded_params.md`

```markdown
## 硬编码参数表
| 参数名 | 值 | 可改性 | 含义 | 来源 |
|--------|-----|--------|------|------|
| BAUD_RATE | 115200 | ⚙️可改 | 串口波特率 | hal_usart.c:xx |
| ... |
```

---

## 覆盖率自检 (分析完成前必须执行)

### A. 源文件覆盖率
1. 对照 `project_context.json` 中的 `business_sources` 列表
2. 确认**每个业务源文件都至少被访问过一次**
3. 如果有遗漏的文件，主动读取并分析

### B. 函数覆盖率 ← 新增
1. 对照 `call_graph_hint.json` 的 `function_defs` 字段
2. 排除系统函数后，计算 `module_analysis.md` 中提到的函数数 / call_graph_hint 中的业务函数总数
3. **目标: >= 90%**
4. 未达标 → 回到源码补充遗漏的函数

### C. 中间文件完整性
1. 确认13个中间文件都已创建
2. 每个文件内容非空

---

## 输出文件清单

分析完成后，`_analysis/` 目录下应包含以下文件:

| 文件 | 内容 | 被哪些文档子skill使用 |
|------|------|---------------------|
| `project_overview.md` | 芯片型号、代码统计、目录结构 | 01_overview, 00_overview |
| `clock_tree.md` | 时钟树完整分析 | 02_hardware |
| `gpio_and_pins.md` | 所有GPIO引脚、重映射 | 02_hardware |
| `peripheral_config.md` | 外设详细配置 | 02_hardware, 04_modules |
| `nvic_priorities.md` | NVIC优先级表 | 02_hardware, 03_architecture |
| `system_init_and_tasks.md` | 启动顺序、任务列表 | 03_architecture |
| `memory_layout.md` | Flash/RAM/Stack/Heap | 03_architecture |
| `module_analysis.md` | 各模块详细分析 | 04_modules |
| `protocol_analysis.md` | 通信协议分析 | 05_protocols |
| `data_flow.md` | 数据流链路 | 08_dataflow |
| `data_structures.md` | 核心数据结构 | 01_overview, 04_modules |
| `hardcoded_params.md` | 硬编码参数 | 06_params |
| `issues_and_risks.md` | BUG、冲突、风险 | 07_issues |
