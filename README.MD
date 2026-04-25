---
name: Vehicle APS
description: 整车高级生产排序系统智能助手插件 (V1.3.9)。允许 Agent 直接调用系统的排序优化、车辆管理、生产时间线查询等 AI 接口。
type: python
---

# Vehicle APS Skill

此插件使 Agent 能够与 **Vehicle APS (整车高级生产排序系统 V1.3.9)** 进行交互。Agent 可以通过此插件执行排序优化、查询工厂状态、调整生产计划、分析生产线时间轴等指令。

## 配置要求

在安装此插件后，您必需确保 `skills/vehicle_aps/config.json` 文件已正确配置以下项：

- `url`: 系统的访问地址（例如 `http://localhost:3000`）。
- `username`: 登录用户名（例如 `Admin`）。
- `password`: 登录密码。
- `verify_ssl`: 是否验证 SSL 证书 (true/false)。如果系统使用自签名证书，请设置为 `false`。

## 安装步骤

### 方法 A：自动安装（推荐）

直接在插件目录运行安装脚本：

```bash
chmod +x skills/vehicle_aps/install_vehicle_aps_cli.sh
./skills/vehicle_aps/install_vehicle_aps_cli.sh
```

脚本将自动执行以下操作：

1. 检测环境并同步文件。
2. 安装必要的 Python 依赖 (`requests`)。
3. **自动配置全局别名 `aps`** (支持 `zsh` 和 `bash`)，让您可以在任何路径下直接使用。

### 方法 B：Windows 自动安装

如果您在 Windows 环境下使用，请打开 PowerShell 并运行：

```powershell
# 如果需要，先赋予执行权限
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 运行安装脚本
.\skills\vehicle_aps\install_vehicle_aps_cli.ps1
```

脚本将自动执行以下操作：

1. 检测环境并同步文件。
2. 安装必要的 Python 依赖 (`requests`)。
3. **自动将 `aps` 函数添加到您的 PowerShell Profile**，让您可以在任何路径下直接使用。

### 方法 C：手动安装

1. **准备插件目录**：
   在 OpenClaw 的插件根目录下创建一个新文件夹：

   ```bash
   mkdir -p ~/.openclaw/skills/vehicle_aps
   ```

2. **同步文件**：
   将 `SKILL.md`、`aps_tool.py` 和 `config.json.example` 复制到上述目录中。

3. **配置连接信息**：
   将 `config.json.example` 重命名为 `config.json`，并填写您的系统访问信息。

4. **安装依赖**：

   ```bash
   pip install requests
   ```

5. **验证与重启**：
   运行以下命令测试连接是否正常：

   ```bash
   python3 ~/.openclaw/skills/vehicle_aps/aps_tool.py --test
   ```

   测试通过后，重启 OpenClaw 即可使用。

## 常驻服务模式 (推荐)

为了避免每次调用时启动 Python 解释器和加载模型带来的延迟，您可以启动常驻服务：

1. **自动启动 (推荐)**：
   您无需手动启动服务。当您第一次运行 `aps_tool.py` 时，它会检测服务是否运行，并在后台自动为您初始化。

2. **手动管理 (可选)**：
   如果您希望手动控制或查看日志，也可以在终端运行：

   ```bash
   python3 skills/vehicle_aps/aps_daemon.py
   ```

## 全局命令模式 (推荐)

在安装并设置别名后，您可以在任何目录下直接输入 `aps` 运行工具：

- **交互式 CLI**：直接输入 `aps`。
- **单条指令**：`aps "查询所有工厂"`。
- **系统配置**：`aps --configure` (交互式配置 URL、API KEY、SSL、语言)。
- **连接测试**：`aps --testrun` (测试连接成功后会自动初始化常驻服务)。
- **查看帮助**：`aps --help`。

在交互模式下，您也可以使用内部指令：

- `/configure`：进入配置模式。
- `/testrun`：运行测试。
- `/set-key <key>`：更新 API KEY。
- `/set-url <url>`：更新后端地址。
- `/lang <zh|en>`：切换语言。

此命令会自动管理常驻服务的生命周期。当您运行 `aps --testrun` 或第一次执行查询时，系统会自动在后台启动常驻内存服务以提高响应速度。

## 功能与调用

当用户提出的要求涉及生产排序、车辆管理、工厂配置、时间线分析时，Agent 应执行以下操作：

1. **确定指令内容**：将用户的需求提炼为一个明确的自然语言指令。
   - *基础查询*："查看 A 工厂目前的资源利用率。"
   - *排序优化*："使用遗传算法对 B 工厂的待排订单进行优化。"
   - *时间线分析*："查询订单 V1002 在总装车间的预计进出站时间。"
   - *配置管理*："列出系统的扩展配置信息。"

2. **运行工具**：在终端通过 `python3` 运行 `aps_tool.py` 脚本：

   ```bash
   python3 skills/vehicle_aps/aps_tool.py "<指令内容>" "zh"
   ```

3. **解释结果**：Agent 应当将响应中的 `answer` 直接向用户进行展示，并在需要时展示 `toolCalled` 或 `toolResult` 的详细数据。

## 使用示例

- **生产查询**：「查询当前总装车间的生产违规情况及瓶颈环节。」
- **订单追踪**：「查看订单 A001 在涂装车间的预计完工时间。」
- **算法执行**：「帮我执行一次层叠优化，锁定前 10 位序列。」
- **配置同步**：「将工厂 A 的基础参数克隆到工厂 B。」

此插件依赖于系统的 AI Agent API：

- 登录端点：`/api/auth/login`
- 接口端点：`/api/agent/command` (支持 RAG 增强与多轮对话上下文)
