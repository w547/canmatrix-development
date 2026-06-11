# DbcTool 一键构建脚本
# 功能: 构建 exe + 打包成可分发的安装包

param(
    [switch]$BuildOnly,      # 仅构建 exe，不打包
    [switch]$Clean           # 清理构建产物
)

$ErrorActionPreference = "Stop"
$AppName = "DbcTool"
$AppVersion = "1.2.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ScriptDir "dist"
$OutputDir = Join-Path $ScriptDir "release"
$SpecFile = Join-Path $ScriptDir "DbcTool.spec"

function Write-Step {
    param([string]$Message)
    Write-Host "[$AppName] " -NoNewline -ForegroundColor Cyan
    Write-Host $Message
}

function Write-OK {
    param([string]$Message)
    Write-Host "  OK  " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Err {
    param([string]$Message)
    Write-Host "  ERR " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

if ($Clean) {
    Write-Step "清理构建产物..."
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "build") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "dist") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "release") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $ScriptDir "__pycache__") -ErrorAction SilentlyContinue
    Write-OK "清理完成"
    exit 0
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  $AppName v$AppVersion 构建脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ─── Step 1: 构建 exe ─────────────────────────────────────
Write-Step "Step 1/3: 使用 PyInstaller 构建 exe..."

if (-not (Test-Path $SpecFile)) {
    Write-Err "找不到 spec 文件: $SpecFile"
    exit 1
}

Remove-Item -Recurse -Force (Join-Path $ScriptDir "build") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $ScriptDir "dist") -ErrorAction SilentlyContinue

$pyiExit = 0
$pyiResult = pyinstaller --clean $SpecFile 2>&1 | ForEach-Object {
    if ($_ -match "completed successfully") { Write-OK "PyInstaller: $_" }
    elseif ($_ -match "ERROR|error|Error") { Write-Err $_ }
    $_
}
if ($LASTEXITCODE -ne 0) {
    Write-Err "PyInstaller 构建失败"
    exit 1
}

$exePath = Join-Path $DistDir "$AppName.exe"
if (-not (Test-Path $exePath)) {
    Write-Err "exe 未生成: $exePath"
    exit 1
}

$exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
Write-OK "exe 构建成功 ($exeSize MB)"

if ($BuildOnly) {
    Write-Host ""
    Write-Host "构建完成! exe 位于: $exePath" -ForegroundColor Green
    exit 0
}

# ─── Step 2: 准备发布目录 ─────────────────────────────────
Write-Step "Step 2/3: 准备发布文件..."

Remove-Item -Recurse -Force $OutputDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Copy-Item $exePath -Destination (Join-Path $OutputDir "$AppName.exe") -Force
Copy-Item (Join-Path $ScriptDir "install.ps1") -Destination (Join-Path $OutputDir "安装.bat") -Force

# 创建中文安装引导脚本
$installBat = @'
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
'@
Set-Content -Path (Join-Path $OutputDir "安装.bat") -Value $installBat -Encoding UTF8

Write-OK "发布文件准备完成"

# ─── Step 3: 打包 ─────────────────────────────────────────
Write-Step "Step 3/3: 创建分发压缩包..."

$zipName = "${AppName}_v${AppVersion}_Windows_x64.zip"
$zipPath = Join-Path $ScriptDir $zipName

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($OutputDir, $zipPath)

$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-OK "压缩包创建完成 ($zipSize MB)"

# ─── 完成 ─────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  构建完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  发布文件:" -ForegroundColor White
Write-Host "    $zipPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "  发布目录:" -ForegroundColor White
Write-Host "    $OutputDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "  用户使用方法:" -ForegroundColor White
Write-Host "    1. 解压 ${zipName}" -ForegroundColor Gray
Write-Host "    2. 双击 '安装.bat' 运行安装程序" -ForegroundColor Gray
Write-Host "    3. 安装完成后从开始菜单或桌面启动" -ForegroundColor Gray
Write-Host ""
