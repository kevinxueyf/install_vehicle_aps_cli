@echo off
setlocal

:: 优先查找全局安装路径
set "GLOBAL_PATH=%USERPROFILE%\.openclaw\skills\vehicle_aps\aps_tool.py"
:: 获取脚本所在目录并定位 aps_tool.py
set "LOCAL_PATH=%~dp0aps_tool.py"

if exist "%GLOBAL_PATH%" (
    set "SKILL_PATH=%GLOBAL_PATH%"
) else if exist "%LOCAL_PATH%" (
    set "SKILL_PATH=%LOCAL_PATH%"
) else (
    set "SKILL_PATH=.\aps_tool.py"
)

if not exist "%SKILL_PATH%" (
    echo ❌ 错误：未找到 aps_tool.py。
    echo 请运行 install_vehicle_aps_cli.ps1 进行安装。
    exit /b 1
)

:: 检查 python 是否可用，优先使用 python，回退到 python3
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%SKILL_PATH%" %*
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        python3 "%SKILL_PATH%" %*
    ) else (
        echo ❌ 错误：未找到 python 或 python3。请确保已安装 Python 并添加到 PATH。
        exit /b 1
    )
)
