@echo off
chcp 65001 >nul
echo 正在打开前端测试页面...
start "" "%~dp0frontend\test.html"
