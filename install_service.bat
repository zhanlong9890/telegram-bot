@echo off
chcp 65001 >nul
echo ========================================
echo Telegram 机器人 Windows 服务安装工具
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

echo [1/4] 检查 Python 安装...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python！
    pause
    exit /b 1
)

python --version
echo.

echo [2/4] 检查 NSSM...
if not exist "nssm" (
    echo [警告] 未找到 NSSM 文件夹
    echo 请下载 NSSM 并解压到当前目录的 nssm 文件夹中
    echo 下载地址: https://nssm.cc/download
    echo.
    pause
    exit /b 1
)

echo [3/4] 获取当前目录...
set "CURRENT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%CURRENT_DIR%bot.py"

echo 工作目录: %CURRENT_DIR%
echo Python: %PYTHON_PATH%
echo 脚本路径: %SCRIPT_PATH%
echo.

echo [4/4] 安装服务...
nssm\win64\nssm.exe install TelegramBot "%PYTHON_PATH%" "%SCRIPT_PATH%"
if %errorLevel% neq 0 (
    echo [错误] 服务安装失败！
    pause
    exit /b 1
)

nssm\win64\nssm.exe set TelegramBot AppDirectory "%CURRENT_DIR%"
nssm\win64\nssm.exe set TelegramBot DisplayName "Telegram Bot Service"
nssm\win64\nssm.exe set TelegramBot Description "Telegram 群管机器人服务"
nssm\win64\nssm.exe set TelegramBot Start SERVICE_AUTO_START
nssm\win64\nssm.exe set TelegramBot AppStdout "%CURRENT_DIR%bot.log"
nssm\win64\nssm.exe set TelegramBot AppStderr "%CURRENT_DIR%bot_error.log"

echo.
echo ========================================
echo 服务安装成功！
echo ========================================
echo.
echo 服务名称: TelegramBot
echo.
echo 管理命令:
echo   启动服务: nssm start TelegramBot
echo   停止服务: nssm stop TelegramBot
echo   重启服务: nssm restart TelegramBot
echo   删除服务: nssm remove TelegramBot confirm
echo.
echo 或者使用 Windows 服务管理器 (services.msc)
echo.
echo 是否现在启动服务？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    nssm\win64\nssm.exe start TelegramBot
    echo 服务已启动！
)
echo.
pause

