@echo off
chcp 65001 >nul
echo ========================================
echo   Telegram 群管机器人启动脚本
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python！
    echo 请先安装 Python 3.9 或更高版本
    pause
    exit /b 1
)
echo ✅ Python 环境正常

echo.
echo [2/3] 检查依赖包...
python -c "import telegram" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  依赖包未安装，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败！
        pause
        exit /b 1
    )
    echo ✅ 依赖包安装完成
) else (
    echo ✅ 依赖包已安装
)

echo.
echo [3/3] 启动机器人...
echo.
echo ========================================
echo   机器人正在启动...
echo   按 Ctrl+C 停止机器人
echo ========================================
echo.

python bot.py

pause

