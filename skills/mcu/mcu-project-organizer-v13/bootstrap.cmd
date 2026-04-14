@echo off
REM ============================================================
REM mcu-project-organizer v10 - One-click Bootstrap
REM Usage: Double-click or run from command line
REM ============================================================
setlocal

set SCRIPT_DIR=%~dp0scripts

if "%~1"=="" (
    set /p PROJECT_ROOT="Enter MCU project root path: "
) else (
    set PROJECT_ROOT=%~1
)

if "%~2"=="" (
    set /p OUT_ROOT="Enter knowledge base output root path: "
) else (
    set OUT_ROOT=%~2
)

if "%~3"=="" (
    set /p TARGET_NAME="Enter Target name (leave empty for auto-select): "
) else (
    set TARGET_NAME=%~3
)

set TEMP_OUT=%OUT_ROOT%\_v10_context
set SNAPSHOT_OUT=%OUT_ROOT%\_v10_snapshot

echo.
echo ============================================================
echo  MCU Project Organizer v10 - Deterministic Extraction
echo ============================================================
echo  Project:  %PROJECT_ROOT%
echo  Output:   %OUT_ROOT%
echo  Target:   %TARGET_NAME%
echo ============================================================
echo.

echo [1/3] Extracting project context...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\01_extract_project_context.ps1" -ProjectRoot "%PROJECT_ROOT%" -OutDir "%TEMP_OUT%" -TargetName "%TARGET_NAME%"
if errorlevel 1 (
    echo [ERROR] Project context extraction failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Exporting source snapshot...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\02_export_source_snapshot.ps1" -ProjectRoot "%PROJECT_ROOT%" -OutDir "%SNAPSHOT_OUT%" -ContextFile "%TEMP_OUT%\project_context.json"
if errorlevel 1 (
    echo [ERROR] Source snapshot export failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Building call graph hint...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%\03_build_call_graph_hint.ps1" -SnapshotDir "%SNAPSHOT_OUT%" -OutDir "%TEMP_OUT%" -ContextFile "%TEMP_OUT%\project_context.json"
if errorlevel 1 (
    echo [ERROR] Call graph hint generation failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Deterministic extraction complete!
echo  Project context:  %TEMP_OUT%\project_context.json
echo  Source snapshot:   %SNAPSHOT_OUT%
echo  Call graph hint:   %TEMP_OUT%\call_graph_hint.json
echo.
echo  Next: Use AI with SKILL.md to perform call-chain analysis
echo ============================================================
pause
