#!/bin/bash

# --- 配置区 ---
SKILL_NAME="vehicle_aps"
# 自动定位当前脚本所在的目录作为源目录
SOURCE_DIR=$(cd "$(dirname "$0")" && pwd)

# --- 远程安装支持 ---
# 如果脚本在临时目录运行且没有 README.MD，则尝试从 GitHub 克隆
if [ ! -f "$SOURCE_DIR/README.MD" ]; then
    echo "🌐 检测到远程执行。正在从 GitHub 克隆完整仓库..."
    if ! command -v git &> /dev/null; then
        echo "❌ 错误：未找到 git，请先安装 git 或手动下载仓库。"
        exit 1
    fi
    TEMP_DIR=$(mktemp -d)
    git clone https://github.com/kevinxueyf/install_vehicle_aps_cli.git "$TEMP_DIR" --quiet
    cd "$TEMP_DIR"
    bash ./install_vehicle_aps_cli.sh
    exit $?
fi

# 智能检测安装路径
if [ -d "$HOME/.openclaw" ]; then
    TARGET_BASE="$HOME/.openclaw/skills"
    INSTALL_TYPE="OpenClaw Skill"
else
    TARGET_BASE="$HOME"
    INSTALL_TYPE="Standalone CLI"
fi

echo "🚀 开始安装 Vehicle APS ($INSTALL_TYPE) ..."

# 1. 检查源文件
if [ ! -f "$SOURCE_DIR/README.MD" ]; then
    echo "❌ 错误：在 $SOURCE_DIR 中未找到插件的核心元数据文件 (README.MD)"
    exit 1
fi

# 2. 创建目标目录
mkdir -p "$TARGET_BASE/$SKILL_NAME"

# 3. 复制文件 (只复制必要的文件，排除脚本自身)
echo "📁 正在同步文件到 $TARGET_BASE/$SKILL_NAME..."
cp "$SOURCE_DIR/README.MD" "$TARGET_BASE/$SKILL_NAME/"
cp "$SOURCE_DIR/aps_tool.py" "$TARGET_BASE/$SKILL_NAME/"
cp "$SOURCE_DIR/aps_daemon.py" "$TARGET_BASE/$SKILL_NAME/"
cp "$SOURCE_DIR/aps" "$TARGET_BASE/$SKILL_NAME/"
cp "$SOURCE_DIR/config.json.example" "$TARGET_BASE/$SKILL_NAME/"

# 3.5 赋予执行权限
chmod +x "$TARGET_BASE/$SKILL_NAME/aps_tool.py"
chmod +x "$TARGET_BASE/$SKILL_NAME/aps_daemon.py"
chmod +x "$TARGET_BASE/$SKILL_NAME/aps"

# 4. 准备配置文件（如果不存在）
if [ ! -f "$TARGET_BASE/$SKILL_NAME/config.json" ]; then
    cp "$SOURCE_DIR/config.json.example" "$TARGET_BASE/$SKILL_NAME/config.json"
    echo "📝 已为您生成默认 config.json，请记得修改配置。"
fi

# 5. 安装依赖
echo "🐍 正在检查并安装 Python 依赖 (requests)..."
if command -v pip &> /dev/null; then
    pip install requests --quiet
elif command -v pip3 &> /dev/null; then
    pip3 install requests --quiet
else
    echo "⚠️  未找到 pip 或 pip3，请手动安装 requests: pip install requests"
fi

# 6. 自动设置别名 (aps)
echo "🔗 正在自动配置 'aps' 命令别名..."
ALIAS_LINE="alias aps='$TARGET_BASE/$SKILL_NAME/aps'"

# 针对 zsh (macOS 默认)
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "alias aps=" "$HOME/.zshrc"; then
        echo "" >> "$HOME/.zshrc"
        echo "# Vehicle APS CLI Alias" >> "$HOME/.zshrc"
        echo "$ALIAS_LINE" >> "$HOME/.zshrc"
        echo "✨ 已将别名添加到 ~/.zshrc"
    else
        # 如果已存在，确保路径是最新的（可选，这里先只做添加）
        echo "ℹ️  ~/.zshrc 中已存在 'aps' 别名，跳过添加。"
    fi
fi

# 针对 bash
if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "alias aps=" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# Vehicle APS CLI Alias" >> "$HOME/.bashrc"
        echo "$ALIAS_LINE" >> "$HOME/.bashrc"
        echo "✨ 已将别名添加到 ~/.bashrc"
    else
        echo "ℹ️  ~/.bashrc 中已存在 'aps' 别名，跳过添加。"
    fi
fi

echo "✅ 安装完成！"
echo "------------------------------------------------"
echo "👉 请在以下路径修改您的连接配置："
echo "   $TARGET_BASE/$SKILL_NAME/config.json"
echo "------------------------------------------------"
echo "💡 提示：重启 OpenClaw 或执行以下命令即可立即使用 'aps'："
echo "   source ~/.zshrc  (如果您使用的是 zsh)"
echo "   source ~/.bashrc (如果您使用的是 bash)"
echo "🛠️  测试命令："
echo "   aps --test"
echo "------------------------------------------------"
