@echo off
chcp 65001 >nul
title DbcTool 安装程序

echo.
echo ============================================
echo   DbcTool v1.2.0 安装程序
echo   CAN数据库可视化工具集
echo ============================================
echo.
echo 正在启动安装...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0install.ps1"
