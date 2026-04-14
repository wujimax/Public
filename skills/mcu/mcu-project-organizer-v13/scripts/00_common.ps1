# ============================================================
# mcu-project-organizer v10 - 公共工具函数
# ============================================================
# Note: No StrictMode to avoid variable scoping issues across if/switch blocks
$ErrorActionPreference = 'Stop'

function New-DirectoryIfMissing([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Get-IsoTimestamp {
    return (Get-Date).ToString('o')
}

function Write-JsonFile([object]$Object, [string]$Path, [int]$Depth = 16) {
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -Encoding UTF8 $Path
}

function Resolve-NormalizedPath([string]$BaseDir, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    $normalized = $Value -replace '/', '\\'
    if ([System.IO.Path]::IsPathRooted($normalized)) {
        return [System.IO.Path]::GetFullPath($normalized)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseDir $normalized))
}

function Get-RelativePathSafe([string]$Root, [string]$Path) {
    try {
        $rootUri = [Uri]((Resolve-Path $Root).Path + [System.IO.Path]::DirectorySeparatorChar)
        $pathUri = [Uri](Resolve-Path $Path).Path
        return [Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString()).Replace('/','\')
    } catch {
        return $Path
    }
}

function Get-PathTag([string]$PathValue) {
    $lower = ($PathValue -replace '/', '\\').ToLowerInvariant()
    if ($lower -match '\\(build|obj|objects|output|out|debug|release)\\') { return 'build_output' }
    if ($lower -match '\\(generated|autogen)\\') { return 'generated' }
    if ($lower -match '\\(test|tests|unittest|unit_test|mock|mocks)\\') { return 'test' }
    if ($lower -match '\\(legacy|old|backup|bak|archive)\\') { return 'legacy' }
    if ($lower -match '\\(libraries|library|cmsis|stdperiph|stdperiph_driver|driverlib|middleware|third_party|third-party|vendor|freertos|lwip|fatfs|mbedtls|usb_lib|u8g2)\\') { return 'third_party' }
    return 'business'
}
