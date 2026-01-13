@echo off
chcp 65001 >nul
echo ========================================
echo   📚 校园二手书 AI 识别 - 启动脚本
echo ========================================
echo.

cd /d %~dp0backend

echo [1/2] 正在获取本机 IP 地址...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set IP=%%a
)
set IP=%IP:~1%
echo.
echo ✅ 本机 IP: %IP%
echo.

:: 检查 .env 文件
if not exist .env (
    echo ⚠️  警告: 未找到 .env 文件，请先配置 API 密钥
    echo.
)

echo ========================================
echo   📱 分享给朋友的步骤:
echo ========================================
echo.
echo   1. 确保你和朋友连接同一个 WiFi
echo   2. 把 frontend/test.html 发给朋友
echo   3. 朋友打开后，API 会自动连接到:
echo      http://%IP%:8000
echo.
echo ========================================
echo.
echo 后端服务地址: http://%IP%:8000
echo API 文档: http://%IP%:8000/docs
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
