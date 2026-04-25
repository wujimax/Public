# ============================================================
# mcu-project-organizer v10 - 合并式项目上下文提取
# 功能: 检测项目类型 + 解析宏定义/源文件/include路径
# 合并了 v9 的 01_detect + 02_parse_uvprojx/uvproj/iar
# ============================================================
param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [string]$TargetName = ''
)

. $PSScriptRoot\00_common.ps1
New-DirectoryIfMissing $OutDir

# ---- 第一步: 检测项目文件 ----
$projectFiles = @(Get-ChildItem -Path $ProjectRoot -Recurse -File -Include *.uvprojx,*.uvproj,*.ewp -ErrorAction SilentlyContinue)
if ($projectFiles.Count -eq 0) {
    throw "在 $ProjectRoot 下未找到 .uvprojx / .uvproj / .ewp 项目文件"
}

# 按优先级排序: uvprojx > uvproj > ewp
$sorted = $projectFiles | Sort-Object @{
    Expression = {
        switch -Regex ($_.Extension) {
            '\.uvprojx$' { 0 }
            '\.uvproj$'  { 1 }
            '\.ewp$'     { 2 }
            default      { 9 }
        }
    }
}

$projectFile = $sorted[0]
$buildSystem = switch -Regex ($projectFile.Extension) {
    '\.uvprojx$' { 'keil_uvprojx' }
    '\.uvproj$'  { 'keil_uvproj' }
    '\.ewp$'     { 'iar_ewp' }
}

Write-Host "[v10] 检测到 $buildSystem : $($projectFile.FullName)"

# ---- 第二步: 解析项目文件 ----
[xml]$xml = Get-Content -Raw -Encoding UTF8 $projectFile.FullName
$projectDir = Split-Path $projectFile.FullName -Parent

$allTargets = @()
$targetNode = $null

if ($buildSystem -in @('keil_uvprojx', 'keil_uvproj')) {
    foreach ($node in @($xml.SelectNodes('//TargetName'))) {
        if ($node.InnerText) { $allTargets += $node.InnerText.Trim() }
    }
    if ($TargetName -eq '') {
        $TargetName = $allTargets[0]
        Write-Host "[v10] Auto-selected first Target: $TargetName"
    }
    $targetNode = $xml.SelectSingleNode("//Target[TargetName='$TargetName']")
    if (-not $targetNode) {
        throw "Target '$TargetName' not found. Available: $($allTargets -join ', ')"
    }
}
elseif ($buildSystem -eq 'iar_ewp') {
    foreach ($configNode in @($xml.project.configuration)) {
        $nameNode = $configNode.SelectSingleNode('./name')
        if ($nameNode -and $nameNode.InnerText) {
            $allTargets += $nameNode.InnerText.Trim()
        }
    }
    if ($TargetName -eq '') { $TargetName = $allTargets[0] }
    foreach ($configNode in @($xml.project.configuration)) {
        $nameNode = $configNode.SelectSingleNode('./name')
        if ($nameNode -and $nameNode.InnerText.Trim() -eq $TargetName) {
            $targetNode = $configNode
            break
        }
    }
    if (-not $targetNode) {
        throw "Target '$TargetName' not found in IAR project. Available: $($allTargets -join ', ')"
    }
}

# ---- 第三步: 提取宏定义、源文件、include路径 ----
$defines = @()
$includePaths = @()
$activeSources = New-Object System.Collections.Generic.List[string]

if ($buildSystem -in @('keil_uvprojx', 'keil_uvproj')) {
    # Keil: Macros
    $defineNode = $targetNode.SelectSingleNode('.//TargetOption/TargetArmAds/Cads/VariousControls/Define')
    if ($defineNode -and $defineNode.InnerText) {
        $defines = @($defineNode.InnerText.Split(',; ', [System.StringSplitOptions]::RemoveEmptyEntries) |
            ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }

    # Keil: 芯片型号 (Device) - V12.1新增
    $deviceName = ''
    $deviceNode = $targetNode.SelectSingleNode('.//TargetOption/TargetCommonOption/Device')
    if ($deviceNode -and $deviceNode.InnerText) {
        $deviceName = $deviceNode.InnerText.Trim()
        Write-Host "  Device: $deviceName"
    }

    # Keil: Flash/RAM配置 - V12.1新增
    $flashStart = ''; $flashSize = ''
    $ramStart = '';   $ramSize = ''

    # 方式1: 从 <Cpu> 节点的内联文本中提取 (Keil4/5通用格式)
    # 格式: IROM(0x08000000,0x10000) IRAM(0x20000000,0x5000)
    $cpuNode = $targetNode.SelectSingleNode('.//TargetOption/TargetCommonOption/Cpu')
    if ($cpuNode -and $cpuNode.InnerText) {
        $cpuText = ($cpuNode.InnerText -replace '[\r\n]+', ' ').Trim()
        if ($cpuText -match 'IROM\s*\(\s*(0x[0-9a-fA-F]+)\s*,\s*(0x[0-9a-fA-F]+)\s*\)') {
            $flashStart = $Matches[1]
            $flashSize = $Matches[2]
        }
        if ($cpuText -match 'IRAM\s*\(\s*(0x[0-9a-fA-F]+)\s*,\s*(0x[0-9a-fA-F]+)\s*\)') {
            $ramStart = $Matches[1]
            $ramSize = $Matches[2]
        }
    }

    # 方式2: 备用 - 从 <IROM1>/<IRAM1> XML标签提取 (部分Keil5项目)
    if (-not $flashStart) {
        $rawXml = $targetNode.OuterXml
        if ($rawXml -match '<IROM1>[\s\S]*?<StartAddress>(0x[0-9a-fA-F]+)</StartAddress>[\s\S]*?<Size>(0x[0-9a-fA-F]+)</Size>') {
            $flashStart = $Matches[1]
            $flashSize = $Matches[2]
        }
        if ($rawXml -match '<IRAM1>[\s\S]*?<StartAddress>(0x[0-9a-fA-F]+)</StartAddress>[\s\S]*?<Size>(0x[0-9a-fA-F]+)</Size>') {
            $ramStart = $Matches[1]
            $ramSize = $Matches[2]
        }
    }

    if ($flashStart) { Write-Host "  Flash: $flashStart, Size=$flashSize" }
    if ($ramStart)   { Write-Host "  RAM:   $ramStart, Size=$ramSize" }

    # Keil: Include 路径
    $includeNode = $targetNode.SelectSingleNode('.//TargetOption/TargetArmAds/Cads/VariousControls/IncludePath')
    if ($includeNode -and $includeNode.InnerText) {
        $includePaths = @($includeNode.InnerText.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries) |
            ForEach-Object { Resolve-NormalizedPath $projectDir $_ } | Where-Object { $_ })
    }
    # Keil: Source files
    $fileNodes = $targetNode.SelectNodes('.//Groups/Group/Files/File')
    foreach ($fileNode in $fileNodes) {
        $filePathNode = $fileNode.SelectSingleNode('./FilePath')
        if ($filePathNode -and $filePathNode.InnerText) {
            $resolved = Resolve-NormalizedPath $projectDir $filePathNode.InnerText
            if ($resolved -and (Test-Path $resolved)) {
                [void]$activeSources.Add($resolved)
            }
        }
    }
}
elseif ($buildSystem -eq 'iar_ewp') {
    # IAR: 宏定义和 include 路径
    $iarOptions = @($targetNode.SelectNodes('.//settings/data/option'))
    foreach ($optionNode in $iarOptions) {
        $optNameNode = $optionNode.SelectSingleNode('./name')
        if (-not $optNameNode) { continue }
        $optName = $optNameNode.InnerText
        if ($optName -eq 'CCDefines') {
            $stateNodes = @($optionNode.SelectNodes('./state'))
            foreach ($stateNode in $stateNodes) {
                if ($stateNode.InnerText) { $defines += $stateNode.InnerText.Trim() }
            }
        }
        elseif ($optName -eq 'CCIncludePath2') {
            $stateNodes = @($optionNode.SelectNodes('./state'))
            foreach ($stateNode in $stateNodes) {
                if ($stateNode.InnerText) {
                    $p = $stateNode.InnerText -replace '\$PROJ_DIR\$', $projectDir
                    $resolved = Resolve-NormalizedPath $projectDir $p
                    if ($resolved) { $includePaths += $resolved }
                }
            }
        }
    }
    # IAR 源文件
    $iarFileNodes = @($xml.SelectNodes('//file'))
    foreach ($fNode in $iarFileNodes) {
        $fNameNode = $fNode.SelectSingleNode('./name')
        if ($fNameNode -and $fNameNode.InnerText) {
            $p = $fNameNode.InnerText -replace '\$PROJ_DIR\$', $projectDir
            $resolved = Resolve-NormalizedPath $projectDir $p
            if ($resolved -and (Test-Path $resolved)) {
                [void]$activeSources.Add($resolved)
            }
        }
    }
}

# ---- 第四步: 分类源文件 ----
$sourceClassification = @()
$businessSources = @()
$thirdPartySources = @()

foreach ($src in $activeSources) {
    $tag = Get-PathTag $src
    $rel = Get-RelativePathSafe $ProjectRoot $src
    $sourceClassification += @{
        absolute_path = $src
        relative_path = $rel
        classification = $tag
    }
    if ($tag -eq 'third_party') { $thirdPartySources += $rel }
    else { $businessSources += $rel }
}

# ---- 第五步: 输出 ----
$runId = "$($projectFile.BaseName)__${TargetName}__$(Get-Date -Format 'yyyyMMdd_HHmmss')" -replace ' ','_'

$context = [ordered]@{
    project_name       = Split-Path $ProjectRoot -Leaf
    project_root       = $ProjectRoot
    build_system       = $buildSystem
    project_file       = $projectFile.FullName
    target_name        = $TargetName
    all_targets        = $allTargets
    device             = if ($deviceName) { $deviceName } else { '' }
    flash_start        = if ($flashStart) { $flashStart } else { '' }
    flash_size         = if ($flashSize)  { $flashSize }  else { '' }
    ram_start          = if ($ramStart)   { $ramStart }   else { '' }
    ram_size           = if ($ramSize)    { $ramSize }    else { '' }
    run_id             = $runId
    active_macros      = $defines
    include_paths      = $includePaths
    total_source_count = $activeSources.Count
    business_count     = $businessSources.Count
    third_party_count  = $thirdPartySources.Count
    generated_at       = Get-IsoTimestamp
    business_sources   = $businessSources
    third_party_sources = $thirdPartySources
    active_sources     = $sourceClassification
}

Write-JsonFile $context (Join-Path $OutDir 'project_context.json')
$activeSources | Set-Content -Encoding UTF8 (Join-Path $OutDir 'active_sources.txt')
$defines | Set-Content -Encoding UTF8 (Join-Path $OutDir 'active_macros.txt')
$includePaths | Set-Content -Encoding UTF8 (Join-Path $OutDir 'include_paths.txt')

Write-Host "[v10] Project context extraction done:"
Write-Host "  Target: $TargetName"
Write-Host "  Macros: $($defines.Count)"
Write-Host ("  Sources: {0} (business: {1}, third_party: {2})" -f $activeSources.Count, $businessSources.Count, $thirdPartySources.Count)
Write-Host "  Include paths: $($includePaths.Count)"
Write-Host "  Run ID: $runId"
Write-Host "  Output: $OutDir"
