@echo off
setlocal enabledelayedexpansion

title Tailscale Manager

pushd "%~dp0"

:: Check if uv is available
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] uv not found -- installing via PowerShell ...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    where uv >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] uv install failed. Install it manually from https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
)

:: Ensure config directory exists for .env file
if not exist "%APPDATA%\tailscale-manager" mkdir "%APPDATA%\tailscale-manager"

echo [*] Running uv sync ...
uv sync
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

echo [*] Launching Tailscale Manager ...
uv run python -m tailscale_manager

popd