# ============================================================
# mcu-project-organizer v10 - 调用图提示生成
# 功能: 用 grep 从业务源文件中提取函数定义和调用关系
#       生成 call_graph_hint.json 辅助 AI 追踪调用链
# 注: 这是文本级粗提取，不是真编译器级解析，但足够辅助 AI
# ============================================================
param(
    [Parameter(Mandatory=$true)][string]$SnapshotDir,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [Parameter(Mandatory=$true)][string]$ContextFile
)

. $PSScriptRoot\00_common.ps1
New-DirectoryIfMissing $OutDir

$ctx = Get-Content -Raw -Encoding UTF8 $ContextFile | ConvertFrom-Json
$srcDir = Join-Path $SnapshotDir 'sources'

# ---- 提取函数定义 ----
# 匹配 C 函数定义: 返回值类型 函数名(参数) 后跟 { 或换行{
$functionDefs = @{}
$allFunctionNames = @()

$businessFiles = @($ctx.active_sources | Where-Object { $_.classification -ne 'third_party' })

foreach ($item in $businessFiles) {
    $relPath = $item.relative_path
    $filePath = Join-Path $srcDir $relPath
    if (-not (Test-Path $filePath)) { continue }
    if ($filePath -notmatch '\.(c|cpp|cc)$') { continue }

    $lines = Get-Content -Encoding UTF8 $filePath -ErrorAction SilentlyContinue
    if (-not $lines) { continue }

    $funcsInFile = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        # 跳过注释行、预处理、空行
        if ($line -match '^\s*(//|/\*|\*|#|$)') { continue }
        # Match C function definition: return_type function_name(
        # Require at least one type keyword before function name
        if ($line -match '^(?:static\s+|extern\s+|inline\s+)?(?:const\s+)?(?:void|unsigned|signed|int|char|short|long|float|double|uint\d+_t|int\d+_t|u8|u16|u32|s8|s16|s32|en_\w+|str_\w+|Stu_\w+|TIMER_\w+|HAL_\w+|GPIO_\w+|ErrorStatus|FunctionalState|FlagStatus|ITStatus|BOOL|bool|UINT8|UINT16|UINT32)(?:\s+(?:unsigned|signed|int|char|short|long|\*)*)*\s+\**\s*(\w+)\s*\(' ) {
            $fname = $Matches[1]
            # Exclude C keywords and common non-function matches
            if ($fname -in @('if','else','while','for','switch','return','sizeof','case','do','goto','break','continue','typedef','struct','enum','union','volatile','register','extern','static','const','defined')) { continue }
            if ($fname.Length -lt 2) { continue }
            # 检查后续几行是否有 { (函数体开始)
            $hasBody = $false
            for ($j = $i; $j -lt [Math]::Min($i + 3, $lines.Count); $j++) {
                if ($lines[$j] -match '\{') { $hasBody = $true; break }
            }
            if ($hasBody) {
                $funcsInFile += @{ name = $fname; line = ($i + 1) }
                $allFunctionNames += $fname
            }
        }
    }

    if ($funcsInFile.Count -gt 0) {
        $functionDefs[$relPath] = $funcsInFile
    }
}

# ---- 提取函数调用关系 ----
$callRelations = @{}

foreach ($item in $businessFiles) {
    $relPath = $item.relative_path
    $filePath = Join-Path $srcDir $relPath
    if (-not (Test-Path $filePath)) { continue }
    if ($filePath -notmatch '\.(c|cpp|cc)$') { continue }

    $content = Get-Content -Raw -Encoding UTF8 $filePath -ErrorAction SilentlyContinue
    if (-not $content) { continue }

    $callsFromFile = @()
    foreach ($fname in $allFunctionNames) {
        # 检查这个文件是否调用了某个函数(排除函数定义自身)
        if ($content -match "(?<!\w)${fname}\s*\(") {
            # 确认不是函数定义本身（定义在 functionDefs 中且是同一个文件）
            $isDefHere = $false
            if ($functionDefs.ContainsKey($relPath)) {
                foreach ($def in $functionDefs[$relPath]) {
                    if ($def.name -eq $fname) { $isDefHere = $true; break }
                }
            }
            if (-not $isDefHere) {
                $callsFromFile += $fname
            }
        }
    }

    if ($callsFromFile.Count -gt 0) {
        $callRelations[$relPath] = $callsFromFile
    }
}

# ---- 生成任务入口追踪提示 ----
# 找到 main 函数所在文件
$mainFile = ''
foreach ($file in $functionDefs.Keys) {
    foreach ($def in $functionDefs[$file]) {
        if ($def.name -eq 'main') {
            $mainFile = $file
            break
        }
    }
    if ($mainFile) { break }
}

# ---- Output ----
$output = [ordered]@{
    main_file          = $mainFile
    function_count     = $allFunctionNames.Count
    file_count         = $functionDefs.Count
    generated_at       = Get-IsoTimestamp
    note               = "Text-level extraction, may have minor false positives. AI should verify against actual source code."
    all_function_names = @($allFunctionNames | Sort-Object -Unique)
    function_defs      = $functionDefs
    call_relations     = $callRelations
}

Write-JsonFile $output (Join-Path $OutDir 'call_graph_hint.json')

Write-Host "[v10] Call graph hint generated:"
Write-Host "  main() in: $mainFile"
Write-Host ("  Functions: {0} (from {1} files)" -f $allFunctionNames.Count, $functionDefs.Count)
Write-Host "  Cross-file calls: $($callRelations.Count) files"
