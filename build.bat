@echo off
setlocal enabledelayedexpansion

title Tailscale Manager - Build

pushd "%~dp0"

:: Check if uv is available
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] uv not found -- installing via PowerShell ...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

:: Sync dependencies (including dev group for flet-cli)
echo [*] Running uv sync ...
uv sync --group dev
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

:: Determine version from pyproject.toml
for /f "tokens=2 delims== " %%a in ('findstr /r "version" pyproject.toml ^| findstr /v "file-version product-version"') do set VERSION=%%~a
if "%VERSION%"=="" set VERSION=0.1.0
set VERSION=%VERSION:"=%

:: Build standalone executable
echo [*] Building Tailscale Manager v%VERSION% ...
.venv\Scripts\flet.exe pack ^
    pack.py ^
    -n "tailscale-manager" ^
    --product-name "Tailscale Manager" ^
    --file-description "Full-featured Tailscale network manager" ^
    --product-version "%VERSION%" ^
    --file-version "%VERSION%.0" ^
    --company-name "tailscale-manager" ^
    --copyright "MIT" ^
    --distpath dist ^
    --onedir ^
    --hidden-import "tailscale_manager" ^
    -y

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [*] Build complete: dist\tailscale-manager\
popd
