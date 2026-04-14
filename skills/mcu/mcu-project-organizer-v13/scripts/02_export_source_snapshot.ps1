# ============================================================
# mcu-project-organizer v10 - 源码快照导出
# 功能: 将活跃源文件和头文件复制到干净的快照目录
# ============================================================
param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [Parameter(Mandatory=$true)][string]$ContextFile
)

. $PSScriptRoot\00_common.ps1
New-DirectoryIfMissing $OutDir

$srcDir = Join-Path $OutDir 'sources'
$hdrDir = Join-Path $OutDir 'headers'
New-DirectoryIfMissing $srcDir
New-DirectoryIfMissing $hdrDir

$ctx = Get-Content -Raw -Encoding UTF8 $ContextFile | ConvertFrom-Json

# ---- 复制源文件 ----
$copiedSources = @()
foreach ($item in $ctx.active_sources) {
    $absPath = $item.absolute_path
    if (-not (Test-Path $absPath)) { continue }
    $rel = Get-RelativePathSafe $ProjectRoot $absPath
    $dest = Join-Path $srcDir $rel
    $destDir = Split-Path -Parent $dest
    if ($destDir) { New-DirectoryIfMissing $destDir }
    Copy-Item -Force $absPath $dest
    $copiedSources += @{ relative_path = $rel; classification = $item.classification }
}

# ---- 复制头文件(从 include 路径) ----
$headerSeen = New-Object 'System.Collections.Generic.HashSet[string]'
$copiedHeaders = @()
foreach ($incPath in $ctx.include_paths) {
    if (-not (Test-Path $incPath)) { continue }
    Get-ChildItem -Path $incPath -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.h', '.hpp', '.inc') } |
        ForEach-Object {
            if (-not $headerSeen.Add($_.FullName)) { return }
            $rel = Get-RelativePathSafe $ProjectRoot $_.FullName
            $dest = Join-Path $hdrDir $rel
            $destDir = Split-Path -Parent $dest
            if ($destDir) { New-DirectoryIfMissing $destDir }
            Copy-Item -Force $_.FullName $dest
            $copiedHeaders += $rel
        }
}

# ---- 输出清单 ----
$manifest = @{
    project_name   = $ctx.project_name
    target_name    = $ctx.target_name
    source_count   = $copiedSources.Count
    header_count   = $copiedHeaders.Count
    sources        = $copiedSources
    headers        = $copiedHeaders
    generated_at   = Get-IsoTimestamp
}

Write-JsonFile $manifest (Join-Path $OutDir 'snapshot_manifest.json')

Write-Host "[v10] Source snapshot exported:"
Write-Host "  Sources: $($copiedSources.Count)"
Write-Host "  Headers: $($copiedHeaders.Count)"
Write-Host "  Output: $OutDir"
