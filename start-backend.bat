@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     AI Job Assistant - 快速启动脚本                   ║
echo ╚════════════════════════════════════════════════════════╝
echo.

echo [1/3] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python,请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [成功] Python 已安装
echo.

echo [2/3] 检查依赖...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [成功] 依赖已安装
)
echo.

echo [3/3] 启动后端服务...
echo.
echo ========================================
echo 后端地址: http://localhost:8002
echo API文档:  http://localhost:8002/docs
echo 健康检查: http://localhost:8002/health
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python run.py
