# Vehicle APS CLI Windows 安装脚本

$SkillName = "vehicle_aps"
$SourceDir = $PSScriptRoot

# 1. 智能检测安装路径
$OpenClawPath = Join-Path $HOME ".openclaw"
if (Test-Path $OpenClawPath) {
    $TargetBase = Join-Path $OpenClawPath "skills"
    $InstallType = "OpenClaw Skill"
} else {
    $TargetBase = $HOME
    $InstallType = "Standalone CLI"
}

Write-Host "🚀 开始安装 Vehicle APS ($InstallType) ..." -ForegroundColor Cyan

# 2. 检查源文件
if (!(Test-Path (Join-Path $SourceDir "SKILL.md"))) {
    Write-Host "❌ 错误：在 $SourceDir 中未找到插件的核心元数据文件 (SKILL.md)" -ForegroundColor Red
    exit
}

# 3. 创建目标目录
$TargetDir = Join-Path $TargetBase $SkillName
if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# 4. 同步文件
Write-Host "📁 正在同步文件到 $TargetDir..."
$FilesToCopy = @("SKILL.md", "aps_tool.py", "aps_daemon.py", "aps", "aps.bat", "config.json.example")
foreach ($File in $FilesToCopy) {
    Copy-Item (Join-Path $SourceDir $File) -Destination $TargetDir -Force
}

# 5. 准备配置文件
$ConfigFile = Join-Path $TargetDir "config.json"
if (!(Test-Path $ConfigFile)) {
    Copy-Item (Join-Path $SourceDir "config.json.example") -Destination $ConfigFile
    Write-Host "📝 已为您生成默认 config.json，请记得修改配置。" -ForegroundColor Yellow
}

# 6. 安装依赖
Write-Host "🐍 正在检查并安装 Python 依赖 (requests)..."
pip install requests --quiet
if ($LASTEXITCODE -ne 0) {
    pip3 install requests --quiet
}

# 7. 自动设置别名 (aps)
Write-Host "🔗 正在自动配置 'aps' 命令别名..."
$AliasFunction = @"

# Vehicle APS CLI Alias
function aps {
    python "$TargetDir\aps_tool.py" `$args
}
"@

# 检查 PowerShell 配置文件
if (!(Test-Path $PROFILE)) {
    New-Item -Type File -Path $PROFILE -Force | Out-Null
}

$ProfileContent = Get-Content $PROFILE
if ($ProfileContent -notmatch "function aps") {
    Add-Content -Path $PROFILE -Value $AliasFunction
    Write-Host "✨ 已将 'aps' 函数添加到您的 PowerShell 配置文件 ($PROFILE)" -ForegroundColor Green
} else {
    Write-Host "ℹ️  PowerShell 配置文件中已存在 'aps'，跳过添加。" -ForegroundColor Gray
}

Write-Host "`n✅ 安装完成！" -ForegroundColor Green
Write-Host "------------------------------------------------"
Write-Host "👉 请在以下路径修改您的连接配置："
Write-Host "   $ConfigFile"
Write-Host "------------------------------------------------"
Write-Host "💡 提示：重启 PowerShell 或执行以下命令即可立即使用 'aps'："
Write-Host "   . `$PROFILE"
Write-Host "🛠️  测试命令："
Write-Host "   aps --test"
Write-Host "------------------------------------------------"
