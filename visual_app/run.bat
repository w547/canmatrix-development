@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   DbcTool 可视化转换工具
echo ========================================
echo.

cd /d "%~dp0"

REM 安装依赖（只安装Flask，使用本地修复版canmatrix）
echo (1/2) 检查依赖...
pip install Flask openpyxl --quiet 2>nul
pip uninstall canmatrix -y --quiet 2>nul

REM 添加src到Python路径，优先使用本地修复版
set PYTHONPATH=%~dp0..\src;%PYTHONPATH%

echo (2/2) 启动服务...
echo.
python app.py

pause
