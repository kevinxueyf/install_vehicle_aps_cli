---
name: Vehicle APS
description: AI Assistant Plugin for Advanced Production Sequencing System (V1.3.9). Allows Agents to directly call system interfaces for sequencing optimization, vehicle management, and production timeline queries.
type: python
---

# Vehicle APS Skill

[中文版](README.MD) | English

This plugin enables Agents to interact with the **Vehicle APS (Advanced Production Sequencing System V1.3.9)**. Agents can use this plugin to perform sequencing optimization, query factory status, adjust production plans, and analyze production line timelines.

## Configuration Requirements

After installing this plugin, ensure that the `skills/vehicle_aps/config.json` file is correctly configured with the following items:

- `url`: System access address (e.g., `http://localhost:3000`).
- `apiKey`: System Access Token (API Key).
- `verify_ssl`: Whether to verify SSL certificates (true/false). Set to `false` if using self-signed certificates.
- `language`: Default interaction language (`zh` or `en`).

## Installation Steps

### Method A: GitHub One-Click Install (Fastest)

No manual download required, execute the following command directly in the terminal:

**Linux / macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/kevinxueyf/install_vehicle_aps_cli/main/install_vehicle_aps_cli.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/kevinxueyf/install_vehicle_aps_cli/main/install_vehicle_aps_cli.ps1 | iex
```

### Method B: Local Automatic Installation

If you have already cloned the repository, run the installation script in the plugin directory:

```bash
chmod +x install_vehicle_aps_cli.sh
./install_vehicle_aps_cli.sh
```

The script will automatically:

1. Detect the environment and sync files.
2. Install necessary Python dependencies (`requests`).
3. **Automatically configure the global alias `aps`** (supports `zsh` and `bash`), allowing you to use it from any path.

### Method C: Windows Automatic Installation (Local)

In a Windows environment, open PowerShell and run:

```powershell
# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Run installation script
.\install_vehicle_aps_cli.ps1
```

The script will automatically:

1. Detect the environment and sync files.
2. Install necessary Python dependencies (`requests`).
3. **Automatically add the `aps` function to your PowerShell Profile**, allowing you to use it from any path.

### Method D: Manual Installation

1. **Prepare Plugin Directory**:
   Create a new folder in the OpenClaw plugin root directory:

   ```bash
   mkdir -p ~/.openclaw/skills/vehicle_aps
   ```

2. **Sync Files**:
   Copy `README.MD`, `aps_tool.py`, and `config.json.example` to the above directory.

3. **Configure Connection**:
   Rename `config.json.example` to `config.json` and fill in your system access info.

4. **Install Dependencies**:

   ```bash
   pip install requests
   ```

5. **Verify and Restart**:
   Run the following command to test the connection:

   ```bash
   python3 ~/.openclaw/skills/vehicle_aps/aps_tool.py --test
   ```

   After passing the test, restart OpenClaw to use the plugin.

## Daemon Mode (Recommended)

To avoid latency from starting the Python interpreter and loading models for each call, you can start a resident service:

1. **Auto-Start (Recommended)**:
   You don't need to start the service manually. When you run `aps_tool.py` for the first time, it will detect if the service is running and automatically initialize it in the background.

2. **Manual Management (Optional)**:
   If you wish to control it manually or view logs, run in the terminal:

   ```bash
   python3 skills/vehicle_aps/aps_daemon.py
   ```

## Global Command Mode (Recommended)

After installation and setting up the alias, you can run the tool directly from any directory:

- **Daemon Management**: 
    - `aps start`: Start the background daemon service.
    - `aps stop`: Stop the background daemon service.
    - `aps restart`: Restart the background daemon service.
    - `aps status`: Check service running status.
- **Interactive CLI**: Enter `aps`.
- **Single Instruction**: `aps "Query all factories"`.
- **System Configuration**: `aps --configure` (interactive config for URL, API KEY, SSL, Language).
- **Connection Test**: `aps --testrun` (automatically starts the daemon service after a successful test).
- **Help**: `aps --help`.

In interactive mode, you can also use internal commands:

- `/configure`: Enter configuration mode.
- `/testrun`: Run connection test.
- `/set-key <key>`: Update API KEY.
- `/set-url <url>`: Update backend URL.
- `/lang <zh|en>`: Switch language.

This command automatically manages the lifecycle of the daemon service. When you run `aps --testrun` or execute a query for the first time, the system will automatically start the resident memory service in the background to improve response speed.

## Features and Usage

When user requests involve production sequencing, vehicle management, factory configuration, or timeline analysis, the Agent should:

1. **Determine Instruction Content**: Refine the user's need into a clear natural language instruction.
   - *Basic Query*: "Check current resource utilization of Factory A."
   - *Sequencing Optimization*: "Optimize pending orders in Factory B using Genetic Algorithm."
   - *Timeline Analysis*: "Query estimated entry/exit times for order V1002 in the General Assembly workshop."
   - *Configuration Management*: "List system extended configuration info."

2. **Run Tool**: Execute the `aps_tool.py` script via `python3`:

   ```bash
   python3 skills/vehicle_aps/aps_tool.py "<instruction>" "en"
   ```

3. **Explain Results**: The Agent should present the `answer` from the response directly to the user, and show detailed `toolCalled` or `toolResult` data if necessary.

## Usage Examples

- **Production Query**: "Check current production violations and bottlenecks in the General Assembly workshop."
- **Order Tracking**: "Check estimated completion time for order A001 in the Painting workshop."
- **Algorithm Execution**: "Perform a cascaded optimization and lock the top 10 sequences."
- **Config Sync**: "Clone basic parameters from Factory A to Factory B."

This plugin relies on the system's AI Agent API:

- Login Endpoint: `/api/auth/login`
- Interface Endpoint: `/api/agent/command` (Supports RAG enhancement and multi-turn conversation context)
