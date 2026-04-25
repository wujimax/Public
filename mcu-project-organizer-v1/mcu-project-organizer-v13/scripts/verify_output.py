# -*- coding: utf-8 -*-
"""
知识库输出验证脚本 - verify_output.py
用法: python verify_output.py <知识库目录> <_v10_snapshot目录>

对AI生成的知识库文档进行结构/完整性/一致性验证。
在SKILL流程的最后一步执行，报告所有未通过的检查项。
"""

import os
import sys
import re
import json
import glob


# ============================================================
# 配置: 期望的文档名称列表 (严格按SKILL模板)
# ============================================================
EXPECTED_DOCS = [
    "00_阅读指南.md",
    "01_项目介绍.md",
    "02_硬件配置.md",
    "03_系统架构.md",
    "04_功能模块.md",
    "05_通信协议.md",
    "06_关键参数表.md",
    "07_已知问题与建议.md",
    "08_数据流与控制流.md",
]

# STM32 常用外设搜索关键词 → 期望在文档中出现的名称
PERIPHERAL_KEYWORDS = {
    "USART": {
        "search": [r"USART_Init", r"USART\d+->", r"USART\d+_IRQHandler"],
        "doc_keyword": "USART",
    },
    "SPI": {
        "search": [r"SPI_Init", r"SPI\d+->"],
        "doc_keyword": "SPI",
    },
    "I2C_HW": {
        "search": [r"I2C_Init\(", r"I2C\d+->"],
        "doc_keyword": "I2C",
    },
    "TIM": {
        "search": [r"TIM_TimeBaseInit", r"TIM_OC\dInit"],
        "doc_keyword": "TIM",
    },
    "ADC": {
        "search": [r"ADC_Init", r"ADC\d+->"],
        "doc_keyword": "ADC",
    },
    "DMA": {
        "search": [r"DMA_Init", r"DMA\d+_Channel"],
        "doc_keyword": "DMA",
    },
    "CAN": {
        "search": [r"CAN_Init\("],
        "doc_keyword": "CAN",
    },
    "IWDG": {
        "search": [r"IWDG_"],
        "doc_keyword": "IWDG",
    },
    "WWDG": {
        "search": [r"WWDG_"],
        "doc_keyword": "WWDG",
    },
    "AFIO": {
        "search": [r"GPIO_PinRemapConfig", r"GPIO_AF_"],
        "doc_keyword": "重映射",
    },
    "EXTI": {
        "search": [r"EXTI_Init"],
        "doc_keyword": "EXTI",
    },
}

# GPIO引脚定义正则
GPIO_PIN_DEFINE_RE = re.compile(
    r"#define\s+\w+(?:_PIN|_Pin)\s+(GPIO_Pin_\d+)", re.IGNORECASE
)
GPIO_PORT_DEFINE_RE = re.compile(
    r"#define\s+\w+(?:_PORT|_Port)\s+(GPIO[A-Z])", re.IGNORECASE
)
GPIO_PIN_DIRECT_RE = re.compile(
    r"GPIO_InitStructure\.GPIO_Pin\s*=\s*(GPIO_Pin_\d+)"
)
GPIO_INIT_CALL_RE = re.compile(
    r"GPIO_Init\s*\(\s*(GPIO[A-Z])"
)


class VerifyResult:
    """验证结果收集器"""

    def __init__(self):
        self.passed = []
        self.warnings = []
        self.failures = []

    def ok(self, msg):
        self.passed.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def fail(self, msg):
        self.failures.append(msg)

    def report(self):
        lines = []
        lines.append("=" * 60)
        lines.append("  知识库验证报告")
        lines.append("=" * 60)
        lines.append("")

        # 统计
        total = len(self.passed) + len(self.warnings) + len(self.failures)
        lines.append(
            f"  总计 {total} 项检查: "
            f"✅{len(self.passed)} 通过  "
            f"⚠️{len(self.warnings)} 警告  "
            f"❌{len(self.failures)} 失败"
        )
        lines.append("")

        if self.failures:
            lines.append("--- ❌ 失败项 (必须修正) ---")
            for i, f in enumerate(self.failures, 1):
                lines.append(f"  {i}. {f}")
            lines.append("")

        if self.warnings:
            lines.append("--- ⚠️ 警告项 (建议检查) ---")
            for i, w in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {w}")
            lines.append("")

        if self.passed:
            lines.append(f"--- ✅ 通过项 ({len(self.passed)}项) ---")
            for p in self.passed:
                lines.append(f"  ✓ {p}")
            lines.append("")

        lines.append("=" * 60)
        if self.failures:
            lines.append("  结论: ❌ 验证未通过, 请修正上述失败项")
        elif self.warnings:
            lines.append("  结论: ⚠️ 验证基本通过, 但有警告项需人工确认")
        else:
            lines.append("  结论: ✅ 全部通过!")
        lines.append("=" * 60)

        return "\n".join(lines)


def read_file_try_encodings(filepath):
    """尝试多种编码读取文件，嵌入式项目常见GB2312/GBK"""
    for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def get_source_files(snapshot_dir):
    """获取snapshot中所有.c和.h源文件"""
    files = []
    for ext in ["*.c", "*.h"]:
        files.extend(glob.glob(os.path.join(snapshot_dir, "**", ext), recursive=True))
    return files


# ============================================================
# 检查1: 文档命名完整性
# ============================================================
def check_doc_naming(kb_dir, result):
    """检查知识库目录是否包含全部9个标准命名文档"""
    existing = set(os.listdir(kb_dir))

    for doc in EXPECTED_DOCS:
        if doc in existing:
            result.ok(f"文档存在: {doc}")
        else:
            result.fail(f"文档缺失: {doc}")

    # 检查是否有非标准命名的.md文件
    expected_set = set(EXPECTED_DOCS)
    for f in existing:
        if f.endswith(".md") and f not in expected_set:
            # 排除task.md等非知识库文件
            if f not in ["task.md", "README.md"]:
                result.warn(f"非标准命名文档: {f} (不在SKILL模板中)")


# ============================================================
# 检查2: GPIO引脚覆盖率
# ============================================================
def check_gpio_coverage(snapshot_dir, kb_dir, result):
    """从源码提取所有GPIO引脚定义，检查02_硬件配置是否覆盖"""

    # 读取02_硬件配置内容
    hw_doc_path = os.path.join(kb_dir, "02_硬件配置.md")
    if not os.path.exists(hw_doc_path):
        result.fail("GPIO检查跳过: 02_硬件配置.md 不存在")
        return

    hw_content = read_file_try_encodings(hw_doc_path)
    if hw_content is None:
        result.fail("GPIO检查跳过: 02_硬件配置.md 无法读取")
        return

    # 从源码提取GPIO引脚定义
    source_files = get_source_files(snapshot_dir)
    found_pins = {}  # pin_name -> [(file, line_content)]

    for fpath in source_files:
        content = read_file_try_encodings(fpath)
        if content is None:
            continue

        fname = os.path.basename(fpath)
        for line in content.split("\n"):
            # 匹配 #define XXX_PIN GPIO_Pin_X
            m = GPIO_PIN_DEFINE_RE.search(line)
            if m:
                pin = m.group(1)  # e.g. GPIO_Pin_5
                pin_num = re.search(r"\d+", pin)
                if pin_num:
                    key = f"Pin_{pin_num.group()}"
                    if key not in found_pins:
                        found_pins[key] = []
                    found_pins[key].append((fname, line.strip()))

            # 匹配 GPIO_InitStructure.GPIO_Pin = GPIO_Pin_X
            m2 = GPIO_PIN_DIRECT_RE.search(line)
            if m2:
                pin = m2.group(1)
                pin_num = re.search(r"\d+", pin)
                if pin_num:
                    key = f"Pin_{pin_num.group()}"
                    if key not in found_pins:
                        found_pins[key] = []
                    found_pins[key].append((fname, line.strip()))

    # 统计
    pin_in_doc = 0
    pin_missing = 0
    for pin_key, sources in found_pins.items():
        # 从GPIO_Pin_X提取数字，检查02文档中是否出现对应的PA/PB/PC + 数字
        pin_num = pin_key.replace("Pin_", "")
        # 检查文档中是否出现 "PA{num}" 或 "PB{num}" 或 "PC{num}" 等
        pattern = re.compile(rf"P[A-Z]{pin_num}\b")
        if pattern.search(hw_content):
            pin_in_doc += 1
        else:
            # 给出具体来源以便排查
            src_info = "; ".join(
                [f"{fname}" for fname, _ in sources[:2]]
            )
            result.warn(
                f"GPIO_Pin_{pin_num} 在源码({src_info})中定义, "
                f"但02_硬件配置中未找到对应引脚(P?{pin_num})"
            )
            pin_missing += 1

    if found_pins:
        total = pin_in_doc + pin_missing
        result.ok(
            f"GPIO引脚覆盖: {pin_in_doc}/{total} "
            f"({pin_in_doc * 100 // total}%)"
        )


# ============================================================
# 检查3: 外设枚举覆盖率
# ============================================================
def check_peripheral_coverage(snapshot_dir, kb_dir, result, context_json=None):
    """在业务源码中搜索外设关键词，检查02/04文档中是否有对应描述"""

    # 读取02和04文档
    doc02_path = os.path.join(kb_dir, "02_硬件配置.md")
    doc04_path = os.path.join(kb_dir, "04_功能模块.md")
    doc02 = read_file_try_encodings(doc02_path) or ""
    doc04 = read_file_try_encodings(doc04_path) or ""
    combined_doc = doc02 + "\n" + doc04

    # 只搜索业务源文件，排除ST标准库
    business_files = []
    if context_json and os.path.exists(context_json):
        for enc in ["utf-8-sig", "utf-8", "gbk"]:
            try:
                with open(context_json, "r", encoding=enc) as f:
                    ctx = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            ctx = {}
        for src in ctx.get("business_sources", []):
            basename = os.path.basename(src)
            # 在snapshot中查找
            for root, dirs, files in os.walk(snapshot_dir):
                if basename in files:
                    business_files.append(os.path.join(root, basename))
                    break

    if not business_files:
        # 降级: 排除常见库目录
        all_files = get_source_files(snapshot_dir)
        lib_dirs = ["stm32f10x_", "core_cm", "misc.", "startup_"]
        business_files = [
            f for f in all_files
            if not any(lib in os.path.basename(f).lower() for lib in lib_dirs)
        ]

    # 合并业务源码内容
    all_source = ""
    for fpath in business_files:
        content = read_file_try_encodings(fpath)
        if content:
            all_source += content + "\n"

    for periph_name, config in PERIPHERAL_KEYWORDS.items():
        # 搜索业务源码中是否使用了该外设
        found_in_source = False
        for pattern in config["search"]:
            if re.search(pattern, all_source):
                found_in_source = True
                break

        if found_in_source:
            # 检查文档中是否提到该外设
            if config["doc_keyword"] in combined_doc:
                result.ok(f"外设 {periph_name}: 源码使用 ✓, 文档提及 ✓")
            else:
                result.fail(
                    f"外设 {periph_name}: 业务源码中使用, "
                    f"但02/04文档中未提及 '{config['doc_keyword']}'"
                )


# ============================================================
# 检查4: 跨文档一致性
# ============================================================
def check_cross_doc_consistency(kb_dir, result):
    """检查各文档间的外设/引脚描述是否一致"""

    doc_contents = {}
    for doc_name in EXPECTED_DOCS:
        path = os.path.join(kb_dir, doc_name)
        if os.path.exists(path):
            doc_contents[doc_name] = read_file_try_encodings(path) or ""

    if not doc_contents:
        result.fail("跨文档检查跳过: 无文档可读")
        return

    # 检查: 01提到的外设关键词在02中是否也有
    doc01 = doc_contents.get("01_项目介绍.md", "")
    doc02 = doc_contents.get("02_硬件配置.md", "")

    periph_keywords = ["OLED", "EEPROM", "USART", "SPI", "I2C", "TIM", "DMA",
                        "NBIoT", "BC26", "MQTT", "蜂鸣器", "LED"]

    if doc01 and doc02:
        for kw in periph_keywords:
            if kw in doc01 and kw not in doc02:
                result.warn(
                    f"01_项目介绍提到 '{kw}', "
                    f"但02_硬件配置中未出现"
                )

    # 检查: 禁止模糊表述 "I2C/SPI"
    for doc_name, content in doc_contents.items():
        if "I2C/SPI" in content or "SPI/I2C" in content:
            result.fail(
                f"{doc_name} 中出现模糊表述 'I2C/SPI', "
                f"必须明确是I2C还是SPI (铁律V11.1)"
            )


# ============================================================
# 检查5: 文档必备内容检查
# ============================================================
def check_doc_required_content(kb_dir, result):
    """检查各文档是否包含SKILL模板要求的必备内容"""

    checks = {
        "00_阅读指南.md": {
            "required": ["项目概况速览", "文档导航"],
            "label": "速览表 + 导航",
        },
        "01_项目介绍.md": {
            "required": ["功能", "目录结构", "struct"],
            "label": "功能列表 + 目录结构 + 数据结构",
        },
        "02_硬件配置.md": {
            "required": ["时钟", "NVIC", "引脚"],
            "label": "时钟树 + NVIC表 + 引脚",
        },
        "03_系统架构.md": {
            "required": ["调度", "启动", "RAM"],
            "label": "调度器 + 启动流程 + 内存",
        },
        "05_通信协议.md": {
            "required": ["帧", "状态"],
            "label": "帧格式 + 状态机",
        },
        "07_已知问题与建议.md": {
            "required": ["P0", "BUG"],
            "label": "问题分级",
        },
        "08_数据流与控制流.md": {
            "required": ["链路", "队列"],
            "label": "数据链路 + 队列表",
        },
    }

    for doc_name, config in checks.items():
        path = os.path.join(kb_dir, doc_name)
        if not os.path.exists(path):
            continue

        content = read_file_try_encodings(path) or ""
        missing = [
            kw for kw in config["required"]
            if kw.lower() not in content.lower()
        ]
        if missing:
            result.warn(
                f"{doc_name} 可能缺少: {config['label']} "
                f"(未找到关键词: {', '.join(missing)})"
            )
        else:
            result.ok(f"{doc_name} 必备内容检查通过")


# ============================================================
# 检查6: 源文件覆盖率
# ============================================================
def check_source_coverage(snapshot_dir, kb_dir, context_json_path, result):
    """检查project_context.json中的业务源文件是否都在文档中被提及"""

    if not os.path.exists(context_json_path):
        result.warn("源文件覆盖检查跳过: project_context.json 不存在")
        return

    for enc in ["utf-8-sig", "utf-8", "gbk"]:
        try:
            with open(context_json_path, "r", encoding=enc) as f:
                ctx = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    else:
        result.warn("无法解析 project_context.json")
        return

    business_sources = ctx.get("business_sources", [])
    if not business_sources:
        result.warn("project_context.json 中无 business_sources 列表")
        return

    # 合并所有文档内容
    all_doc_content = ""
    for doc_name in EXPECTED_DOCS:
        path = os.path.join(kb_dir, doc_name)
        if os.path.exists(path):
            content = read_file_try_encodings(path) or ""
            all_doc_content += content + "\n"

    covered = 0
    for src in business_sources:
        # 取文件名(不含路径)
        basename = os.path.basename(src).replace("\\", "/").split("/")[-1]
        name_no_ext = os.path.splitext(basename)[0]

        if basename in all_doc_content or name_no_ext in all_doc_content:
            covered += 1
        else:
            result.warn(f"业务源文件 {basename} 未在任何文档中被提及")

    if business_sources:
        rate = covered * 100 // len(business_sources)
        if rate == 100:
            result.ok(
                f"源文件覆盖率: {covered}/{len(business_sources)} (100%)"
            )
        else:
            result.fail(
                f"源文件覆盖率: {covered}/{len(business_sources)} ({rate}%)"
            )


# ============================================================
# 检查7: 宏定义引用验证 (防止"已定义未使用"的宏被错误引用)
# ============================================================
MACRO_DEFINE_RE = re.compile(
    r"#define\s+([A-Z_][A-Z0-9_]+)\s+(.+)", re.IGNORECASE
)
# 排除常见的头文件保护宏和标准库宏
MACRO_EXCLUDE_PREFIXES = (
    "_", "__", "STM32", "USE_", "HSE_", "HSI_", "assert_param",
)


def check_macro_actual_usage(snapshot_dir, kb_dir, result):
    """检查: 文档中提到的宏是否在.c源文件中被实际引用"""

    source_files = get_source_files(snapshot_dir)

    # 分离 .h 和 .c 文件
    h_files = [f for f in source_files if f.endswith(".h")]
    c_files = [f for f in source_files if f.endswith(".c")]

    # 排除标准库头文件
    lib_keywords = ["stm32f10x_", "core_cm", "misc.h", "system_stm32"]
    h_files = [
        f for f in h_files
        if not any(kw in os.path.basename(f).lower() for kw in lib_keywords)
    ]
    c_files_biz = [
        f for f in c_files
        if not any(kw in os.path.basename(f).lower() for kw in lib_keywords)
    ]

    # 步骤1: 从业务 .h 文件提取所有自定义宏
    macros = {}  # macro_name -> (value, source_file)
    for hf in h_files:
        content = read_file_try_encodings(hf)
        if not content:
            continue
        fname = os.path.basename(hf)
        for line in content.split("\n"):
            m = MACRO_DEFINE_RE.match(line.strip())
            if m:
                name = m.group(1)
                value = m.group(2).strip()
                # 排除头文件保护宏等
                if any(name.startswith(p) for p in MACRO_EXCLUDE_PREFIXES):
                    continue
                # 排除没有实际值的宏(如 #define _RFD_H)
                if not value or value.startswith("//"):
                    continue
                macros[name] = (value, fname)

    if not macros:
        result.ok("宏引用检查: 未发现业务头文件中的自定义宏")
        return

    # 步骤2: 在 .c 文件中搜索每个宏的实际引用
    all_c_content = ""
    for cf in c_files_biz:
        content = read_file_try_encodings(cf)
        if content:
            # 去掉 #define 行本身，只保留使用行
            lines = [
                ln for ln in content.split("\n")
                if not ln.strip().startswith("#define")
            ]
            all_c_content += "\n".join(lines) + "\n"

    unused_macros = []
    for name, (value, src) in macros.items():
        # 搜索宏名(作为独立单词)
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        if not pattern.search(all_c_content):
            unused_macros.append((name, value, src))

    # 步骤3: 检查未引用的宏是否出现在知识库文档中
    all_doc_content = ""
    for doc_name in EXPECTED_DOCS:
        path = os.path.join(kb_dir, doc_name)
        if os.path.exists(path):
            content = read_file_try_encodings(path) or ""
            all_doc_content += content + "\n"

    warned = 0
    for name, value, src in unused_macros:
        if name in all_doc_content:
            # 检查文档中是否已标注为"未引用"
            if "未引用" in all_doc_content or "未使用" in all_doc_content:
                continue
            result.warn(
                f"宏 {name}={value} (定义于{src}) 在.c代码中未被引用, "
                f"但出现在知识库文档中。请确认文档描述是否准确"
            )
            warned += 1

    if warned == 0:
        result.ok(
            f"宏引用检查: 扫描{len(macros)}个业务宏, "
            f"未发现文档中引用了未使用的宏"
        )


# ============================================================
# 检查8: 函数覆盖率检查 (V12.1 新增)
# ============================================================
# 不要求覆盖的系统函数
SYSTEM_FUNCTIONS_EXCLUDE = {
    # 异常处理器
    "NMI_Handler", "HardFault_Handler", "MemManage_Handler",
    "BusFault_Handler", "UsageFault_Handler", "SVC_Handler",
    "DebugMon_Handler", "PendSV_Handler",
    # 系统时钟配置
    "SystemInit", "SetSysClock", "SetSysClockTo24", "SetSysClockTo36",
    "SetSysClockTo48", "SetSysClockTo56", "SetSysClockTo72",
    "SetSysClockToHSE", "SystemCoreClockUpdate", "SystemInit_ExtMemCtl",
}


def check_function_coverage(kb_dir, context_dir, result):
    """从 call_graph_hint.json 提取业务函数，检查 04_功能模块.md 中的覆盖率"""

    # 寻找 call_graph_hint.json
    cg_path = os.path.join(context_dir, "call_graph_hint.json")
    if not os.path.exists(cg_path):
        result.warn("函数覆盖率检查跳过: call_graph_hint.json 不存在")
        return

    # 读取 call_graph_hint.json
    for enc in ["utf-8-sig", "utf-8", "gbk"]:
        try:
            with open(cg_path, "r", encoding=enc) as f:
                cg = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    else:
        result.warn("无法解析 call_graph_hint.json")
        return

    function_defs = cg.get("function_defs", {})
    if not function_defs:
        result.warn("call_graph_hint.json 中无 function_defs")
        return

    # 提取所有业务函数名（排除系统函数和标准库文件）
    lib_file_keywords = ["stm32f10x_", "core_cm", "misc.", "startup_",
                         "system_stm32"]
    business_functions = []  # (func_name, source_file)

    for filepath, funcs in function_defs.items():
        basename = os.path.basename(filepath).lower()
        # 跳过标准库文件
        if any(kw in basename for kw in lib_file_keywords):
            continue
        for func_info in funcs:
            fname = func_info.get("name", "")
            # 跳过系统函数
            if fname in SYSTEM_FUNCTIONS_EXCLUDE:
                continue
            # 跳过明显的误提取（如 "char" 等关键字）
            if fname in {"char", "void", "int", "uint8_t", "uint16_t", "uint32_t"}:
                continue
            business_functions.append((fname, os.path.basename(filepath)))

    if not business_functions:
        result.warn("函数覆盖率检查跳过: 未找到业务函数")
        return

    # 读取 04_功能模块.md
    doc04_path = os.path.join(kb_dir, "04_功能模块.md")
    if not os.path.exists(doc04_path):
        result.fail("函数覆盖率检查跳过: 04_功能模块.md 不存在")
        return

    doc04_content = read_file_try_encodings(doc04_path) or ""

    # 检查每个函数是否在文档中出现
    covered = []
    missing = []
    for fname, src_file in business_functions:
        if fname in doc04_content:
            covered.append(fname)
        else:
            missing.append((fname, src_file))

    total = len(business_functions)
    covered_count = len(covered)
    rate = covered_count * 100 // total if total > 0 else 0

    if rate >= 90:
        result.ok(
            f"函数覆盖率: {covered_count}/{total} ({rate}%)"
        )
    elif rate >= 70:
        result.warn(
            f"函数覆盖率偏低: {covered_count}/{total} ({rate}%). "
            f"遗漏函数: {', '.join(f[0] for f in missing[:10])}"
            + (f" 等{len(missing)}个" if len(missing) > 10 else "")
        )
    else:
        result.fail(
            f"函数覆盖率过低: {covered_count}/{total} ({rate}%). "
            f"遗漏函数: {', '.join(f[0] for f in missing[:15])}"
            + (f" 等{len(missing)}个" if len(missing) > 15 else "")
        )

def main():
    if len(sys.argv) < 3:
        print("用法: python verify_output.py <知识库目录> <_v10_snapshot目录>")
        print("示例: python verify_output.py ./项目3 ./项目3/_v10_snapshot")
        sys.exit(1)

    kb_dir = sys.argv[1]
    snapshot_dir = sys.argv[2]

    # 可选: project_context.json路径
    context_json = os.path.join(
        os.path.dirname(snapshot_dir.rstrip("/\\")),
        "_v10_context", "project_context.json"
    )
    # 也尝试和snapshot同级
    if not os.path.exists(context_json):
        context_json = os.path.join(
            snapshot_dir, "..", "_v10_context", "project_context.json"
        )
    if not os.path.exists(context_json):
        # 直接在知识库目录找
        for root, dirs, files in os.walk(os.path.dirname(kb_dir)):
            if "project_context.json" in files:
                context_json = os.path.join(root, "project_context.json")
                break

    if not os.path.isdir(kb_dir):
        print(f"错误: 知识库目录不存在: {kb_dir}")
        sys.exit(1)
    if not os.path.isdir(snapshot_dir):
        print(f"错误: snapshot目录不存在: {snapshot_dir}")
        sys.exit(1)

    print(f"知识库目录: {kb_dir}")
    print(f"源码目录:   {snapshot_dir}")
    if os.path.exists(context_json):
        print(f"上下文文件: {context_json}")
    print()

    result = VerifyResult()

    # 执行所有检查
    check_doc_naming(kb_dir, result)
    check_gpio_coverage(snapshot_dir, kb_dir, result)
    check_peripheral_coverage(snapshot_dir, kb_dir, result, context_json)
    check_cross_doc_consistency(kb_dir, result)
    check_doc_required_content(kb_dir, result)
    check_source_coverage(snapshot_dir, kb_dir, context_json, result)
    check_macro_actual_usage(snapshot_dir, kb_dir, result)

    # V12.1 新增: 函数覆盖率检查
    context_dir = os.path.dirname(context_json) if os.path.exists(context_json) else None
    if context_dir:
        check_function_coverage(kb_dir, context_dir, result)

    # V12.1 新增: 芯片型号验证
    if os.path.exists(context_json):
        for enc in ["utf-8-sig", "utf-8", "gbk"]:
            try:
                with open(context_json, "r", encoding=enc) as f:
                    ctx = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            ctx = {}
        device = ctx.get("device", "")
        if device:
            doc02_path = os.path.join(kb_dir, "02_硬件配置.md")
            if os.path.exists(doc02_path):
                doc02 = read_file_try_encodings(doc02_path) or ""
                if device in doc02:
                    result.ok(f"芯片型号验证: {device} 在02文档中出现 ✅")
                else:
                    result.fail(
                        f"芯片型号错误: project_context.json 中为 {device}, "
                        f"但02_硬件配置.md 中未出现该型号"
                    )

    # 输出报告 (强制UTF-8避免Windows GBK控制台编码问题)
    report = result.report()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(report)

    # 保存报告到知识库目录
    report_path = os.path.join(kb_dir, "_verify_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {report_path}")

    # 返回码: 有失败=1, 仅警告=0
    sys.exit(1 if result.failures else 0)


if __name__ == "__main__":
    main()
