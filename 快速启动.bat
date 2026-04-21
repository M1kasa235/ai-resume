@echo off
chcp 65001 >nul
echo ========================================
echo   AI Job Assistant - 快速启动脚本
echo ========================================
echo.

REM 检查 Python
echo [1/4] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python 已安装
echo.

REM 检查 Node.js
echo [2/4] 检查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Node.js，请先安装 Node.js 16+
    pause
    exit /b 1
)
echo ✅ Node.js 已安装
echo.

REM 启动后端
echo [3/4] 启动后端服务...
start "AI Job Assistant - Backend" cmd /k "cd /d %~dp0 && python run.py"
echo ⏳ 等待后端启动...
timeout /t 5 /nobreak >nul
echo.

REM 启动前端
echo [4/4] 启动前端服务...
start "AI Job Assistant - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.

echo ========================================
echo   服务启动中...
echo ========================================
echo.
echo 后端 API: http://localhost:8002
echo 前端应用: http://localhost:5173
echo API 文档: http://localhost:8002/docs
echo.
echo 提示: 
echo - 请确保 MySQL 服务正在运行
echo - 请确保数据库 'ai_job' 已创建
echo - 两个命令行窗口会自动打开
echo - 按 Ctrl+C 可以停止服务
echo.
pause
