# DbcTool 安装脚本
# 以管理员身份运行此脚本即可安装
# 或者直接双击运行（会自动请求管理员权限）

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$AppName = "DbcTool"
$AppVersion = "1.2.0"
$InstallDir = "$env:LOCALAPPDATA\Programs\$AppName"
$ExeName = "DbcTool.exe"
$ShortcutName = "$AppName.lnk"

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Request-Admin {
    if (-not (Test-Admin)) {
        Write-Host "正在请求管理员权限..." -ForegroundColor Yellow
        $arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$PSCommandPath`""
        if ($Uninstall) { $arguments += " -Uninstall" }
        Start-Process powershell -Verb RunAs -ArgumentList $arguments
        exit 0
    }
}

function Write-Step {
    param([string]$Message, [string]$Status = "")
    Write-Host "[$AppName] " -NoNewline -ForegroundColor Cyan
    Write-Host $Message -NoNewline
    if ($Status) {
        Write-Host " $Status" -ForegroundColor Green
    } else {
        Write-Host ""
    }
}

function Uninstall-App {
    Write-Step "开始卸载 $AppName v$AppVersion..."

    $shortcuts = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\$ShortcutName",
        "$env:PUBLIC\Desktop\$ShortcutName",
        "$env:USERPROFILE\Desktop\$ShortcutName"
    )
    foreach ($sc in $shortcuts) {
        if (Test-Path $sc) {
            Remove-Item $sc -Force
            Write-Step "已删除快捷方式: $sc"
        }
    }

    if (Test-Path $InstallDir) {
        Remove-Item $InstallDir -Recurse -Force
        Write-Step "已删除安装目录: $InstallDir"
    }

    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
    if (Test-Path $regPath) {
        Remove-Item $regPath -Recurse -Force
        Write-Step "已删除注册表项"
    }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  $AppName 卸载完成!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "按 Enter 键退出"
}

function Install-App {
    Write-Step "开始安装 $AppName v$AppVersion..."

    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    $sourceExe = Join-Path $PSScriptRoot $ExeName
    if (-not (Test-Path $sourceExe)) {
        Write-Host "错误: 找不到 $ExeName，请确保安装脚本与 exe 在同一目录" -ForegroundColor Red
        Read-Host "按 Enter 键退出"
        exit 1
    }

    Copy-Item $sourceExe -Destination (Join-Path $InstallDir $ExeName) -Force
    Write-Step "已复制程序文件到: $InstallDir"

    $targetExe = Join-Path $InstallDir $ExeName

    $startMenuDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut("$startMenuDir\$ShortcutName")
    $shortcut.TargetPath = $targetExe
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "DbcTool - CAN数据库可视化工具集"
    $shortcut.Save()
    Write-Step "已创建开始菜单快捷方式"

    $desktopShortcut = "$env:PUBLIC\Desktop\$ShortcutName"
    try {
        $sc2 = $WScriptShell.CreateShortcut($desktopShortcut)
        $sc2.TargetPath = $targetExe
        $sc2.WorkingDirectory = $InstallDir
        $sc2.Description = "DbcTool - CAN数据库可视化工具集"
        $sc2.Save()
        Write-Step "已创建桌面快捷方式"
    } catch {
        $desktopShortcut = "$env:USERPROFILE\Desktop\$ShortcutName"
        $sc2 = $WScriptShell.CreateShortcut($desktopShortcut)
        $sc2.TargetPath = $targetExe
        $sc2.WorkingDirectory = $InstallDir
        $sc2.Description = "DbcTool - CAN数据库可视化工具集"
        $sc2.Save()
        Write-Step "已创建桌面快捷方式"
    }

    $uninstallScript = Join-Path $InstallDir "uninstall.ps1"
    Copy-Item $PSCommandPath -Destination $uninstallScript -Force

    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
    if (-not (Test-Path $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }
    Set-ItemProperty -Path $regPath -Name "DisplayName" -Value $AppName
    Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value $AppVersion
    Set-ItemProperty -Path $regPath -Name "Publisher" -Value "DbcTool"
    Set-ItemProperty -Path $regPath -Name "DisplayIcon" -Value $targetExe
    Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$uninstallScript`" -Uninstall"
    Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $InstallDir
    Set-ItemProperty -Path $regPath -Name "NoModify" -Value 1
    Set-ItemProperty -Path $regPath -Name "NoRepair" -Value 1
    Write-Step "已注册到系统（可在 设置->应用 中卸载）"

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  $AppName v$AppVersion 安装完成!" -ForegroundColor Green
    Write-Host "  安装位置: $InstallDir" -ForegroundColor White
    Write-Host "  快捷方式已添加到开始菜单和桌面" -ForegroundColor White
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""

    $startApp = Read-Host "是否立即启动 $AppName？(Y/n)"
    if ($startApp -ne 'n' -and $startApp -ne 'N') {
        Start-Process $targetExe
    } else {
        Read-Host "按 Enter 键退出"
    }
}

# ─── 主入口 ────────────────────────────────────────────────

$host.UI.RawUI.WindowTitle = "$AppName 安装程序 v$AppVersion"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  $AppName v$AppVersion 安装程序" -ForegroundColor Cyan
Write-Host "  CAN数据库可视化工具集" -ForegroundColor DarkCyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($Uninstall) {
    Request-Admin
    Uninstall-App
} else {
    Request-Admin
    Install-App
}
