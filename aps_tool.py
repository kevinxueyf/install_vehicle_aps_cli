import requests
import json
import sys
import os
import argparse
import subprocess
import time

# 获取脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
DAEMON_URL = "http://127.0.0.1:5005/command"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: 配置文件未找到：{CONFIG_PATH}")
        print("请将 config.json.example 重命名为 config.json 并填写配置。")
        sys.exit(1)
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error: 无法解析配置文件：{str(e)}")
        sys.exit(1)

def safe_json_decode(res, label):
    try:
        return res.json()
    except Exception:
        print(f"Error: {label} 返回了非 JSON 响应。")
        print(f"状态码: {res.status_code}")
        print(f"内容预览: {res.text[:200]}...")
        sys.exit(1)

def start_daemon():
    """在后台启动常驻服务"""
    daemon_script = os.path.join(BASE_DIR, 'aps_daemon.py')
    try:
        # 使用 subprocess.Popen 启动，不等待其结束
        # stdout/stderr 重定向到 devnull 以免干扰终端
        kwargs = {}
        if os.name == 'nt':
            # Windows 特有的脱离方式
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            # Unix 特有的脱离方式
            kwargs['start_new_session'] = True

        subprocess.Popen(
            [sys.executable, daemon_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs
        )
        # 给一点时间让服务初始化（加载模型等）
        time.sleep(1.5)
    except Exception as e:
        print(f"Warning: 尝试启动常驻服务失败: {e}")

def call_via_daemon(command, lang='zh', retry=True):
    """尝试通过常驻服务调用"""
    health_url = DAEMON_URL.replace('/command', '/health')
    try:
        # 1. 首先尝试一个极短时间的健康检查 (0.5s)
        # 如果健康检查通过，说明服务在线
        requests.get(health_url, timeout=0.5)
        
        # 2. 服务在线，发送指令，并给予充足的后端处理时间 (60s)
        payload = {"command": command, "lang": lang}
        res = requests.post(DAEMON_URL, json=payload, timeout=60)
        if res.status_code == 200:
            return res.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        # 只有在健康检查失败（服务未启动）且允许重试时才尝试启动
        if retry:
            print("🕒 检测到服务未启动，正在自动初始化常驻服务...")
            start_daemon()
            return call_via_daemon(command, lang, retry=False)
    except Exception:
        return None

def stop_daemon():
    """停止常驻服务"""
    shutdown_url = DAEMON_URL.replace('/command', '/shutdown')
    try:
        requests.post(shutdown_url, timeout=2)
        print("✅ Vehicle APS 常驻服务已停止。")
        return True
    except:
        print("❌ 无法连接到服务，服务可能未启动。")
        return False

def check_status(silent=False):
    """检查常驻服务运行状态"""
    health_url = DAEMON_URL.replace('/command', '/health')
    try:
        res = requests.get(health_url, timeout=1)
        if res.status_code == 200:
            if not silent:
                print("✅ Vehicle APS 常驻服务正在运行。")
                print(f"📍 监听地址: {DAEMON_URL.replace('/command', '')}")
            return True
    except:
        if not silent:
            print("❌ Vehicle APS 常驻服务未启动。")
    return False

def format_output(data, raw=False):
    """格式化输出结果"""
    if raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # 提取核心回答
    answer = data.get('answer', '')
    if not answer:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print("\n" + "─"*50)
    print(answer)
    
    # 如果有执行工具，显示工具状态
    if data.get('usedTool'):
        status = "成功" if data.get('toolName') == 'success' else "失败"
        print(f"\n🛠️  工具执行: {data.get('toolCalled', '未知')} ({status})")
    
    # 如果使用了 RAG，显示来源提示
    if data.get('usedRag'):
        print(f"📚 参考了 {len(data.get('ragResults', []))} 条知识库内容")
    
    print("─"*50 + "\n")

def aps_call(command, lang='zh', is_test=False, raw=False):
    """调用智能体接口"""
    # 优先尝试常驻服务
    if not is_test:
        daemon_res = call_via_daemon(command, lang)
        if daemon_res:
            if daemon_res.get('success'):
                format_output(daemon_res.get('data'), raw)
                return
            else:
                print(f"Error: 指令执行失败 (via Daemon)：{daemon_res.get('message')}")
                sys.exit(1)

    # 如果常驻服务不可用，或处于测试模式，走原始逻辑 (Fallback)
    config = load_config()
    base_url = config.get('url', '').rstrip('/')
    if base_url.endswith('/api'):
        base_url = base_url[:-4]
        
    username = config.get('username')
    password = config.get('password')
    api_key = config.get('apiKey')
    verify_ssl = config.get('verify_ssl', True)

    if not api_key and not all([username, password]):
        print("Error: 配置文件中 API KEY 或 用户名/密码 缺失。")
        sys.exit(1)

    if is_test:
        print(f"🔍 正在测试连接到: {base_url} (Fallback 模式)")

    try:
        # 步骤 1：准备请求头
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key
            if is_test: print("✅ 使用 API KEY 进行认证。")
        else:
            # 获取 Token (旧逻辑)
            login_url = f"{base_url}/api/auth/login"
            login_payload = {"id": username, "password": password}
            login_res = requests.post(login_url, json=login_payload, timeout=10, verify=verify_ssl)
            login_data = safe_json_decode(login_res, "登录接口")
            if not login_data.get('success'):
                print(f"Error: 登录失败：{login_data.get('message')}")
                sys.exit(1)
            token = login_data.get('token')
            headers["Authorization"] = f"Bearer {token}"
            if is_test: print("✅ 登录成功，已获取 Token。")
            
        # 步骤 2：执行指令
        agent_url = f"{base_url}/api/agent/command"
        test_command = "列出系统中的工厂" if is_test else command
        agent_payload = {"command": test_command, "lang": lang}
        
        agent_res = requests.post(agent_url, json=agent_payload, headers=headers, timeout=60, verify=verify_ssl)
        agent_data = safe_json_decode(agent_res, "智能体接口")
        
        if agent_data.get('success'):
            if is_test:
                print("✅ 智能体接口调用成功！系统运行正常。")
            format_output(agent_data.get('data'), raw)
        else:
            print(f"Error: 指令执行失败：{agent_data.get('message')}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: 发生错误: {str(e)}")
        sys.exit(1)

UI_STRINGS = {
    'zh': {
        'welcome_title': "🚗 欢迎使用 Vehicle APS 交互式命令行 (CLI) 模式",
        'tip_label': "💡 提示:",
        'tip_input': "直接输入自然语言指令即可进行查询或操作",
        'tip_help': "输入 '/help' 查看帮助",
        'tip_exit': "输入 '/exit' 或 '/quit' 退出",
        'tip_history': "支持上下方向键查看历史记录",
        'help_title': "[帮助手册]",
        'help_example': "指令示例: '列出所有工厂', '查询订单 V1002'",
        'help_lang': "切换语言: 输入 '/lang en' 或 '/lang zh'",
        'help_key': "更新 API KEY: 输入 '/set-key <your_key>'",
        'help_url': "更新 URL 地址: 输入 '/set-url <your_url>'",
        'help_config': "交互式配置: 输入 '/configure'",
        'help_test': "测试连接并启动服务: 输入 '/testrun'",
        'help_exit': "退出命令: /exit, /quit",
        'lang_switched': "✅ 语言已切换为: ",
        'key_updated': "✅ API KEY 已更新并保存。",
        'url_updated': "✅ URL 地址已更新并保存。",
        'config_start': "⚙️  开始进行系统配置...",
        'config_done': "✅ 配置已保存。",
        'test_start': "🧪 正在启动连接测试与服务初始化...",
        'lang_unsupported': "❌ 不支持的语言，请使用 'zh' 或 'en'",
        'exit_msg': "👋 再见！",
        'error_msg': "❌ 运行出错: "
    },
    'en': {
        'welcome_title': "🚗 Welcome to Vehicle APS Interactive CLI Mode",
        'tip_label': "💡 Tips:",
        'tip_input': "Enter natural language instructions for queries or operations",
        'tip_help': "Type '/help' for assistance",
        'tip_exit': "Type '/exit' or '/quit' to leave",
        'tip_history': "Use Up/Down arrows for command history",
        'help_title': "[Help Manual]",
        'help_example': "Examples: 'List all factories', 'Query order V1002'",
        'help_lang': "Switch Language: Type '/lang en' or '/lang zh'",
        'help_key': "Update API KEY: Type '/set-key <your_key>'",
        'help_url': "Update URL Address: Type '/set-url <your_url>'",
        'help_config': "Interactive Config: Type '/configure'",
        'help_test': "Test Connection & Start Service: Type '/testrun'",
        'help_exit': "Exit: /exit, /quit",
        'lang_switched': "✅ Language switched to: ",
        'key_updated': "✅ API KEY updated and saved.",
        'url_updated': "✅ URL address updated and saved.",
        'config_start': "⚙️  Starting system configuration...",
        'config_done': "✅ Configuration saved.",
        'test_start': "🧪 Starting connection test and service initialization...",
        'lang_unsupported': "❌ Unsupported language, please use 'zh' or 'en'",
        'exit_msg': "👋 Goodbye!",
        'error_msg': "❌ Error: "
    }
}

def interactive_mode(lang='zh'):
    """交互式 CLI 模式"""
    try:
        import readline
    except ImportError:
        pass

    def print_welcome(l):
        s = UI_STRINGS.get(l, UI_STRINGS['zh'])
        print("\n" + "="*50)
        print(s['welcome_title'])
        print("="*50)
        print(s['tip_label'])
        print(f"  - {s['tip_input']}")
        print(f"  - {s['tip_help']}")
        print(f"  - {s['tip_exit']}")
        print(f"  - {s['tip_history']}")
        print("="*50 + "\n")

    print_welcome(lang)

    while True:
        s = UI_STRINGS.get(lang, UI_STRINGS['zh'])
        try:
            user_input = input(f"APS ({lang}) > ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                print(s['exit_msg'])
                break
            
            if user_input.lower() == '/help':
                print(f"\n{s['help_title']}")
                print(f"  - {s['help_example']}")
                print(f"  - {s['help_lang']}")
                print(f"  - {s['help_key']}")
                print(f"  - {s['help_url']}")
                print(f"  - {s['help_config']}")
                print(f"  - {s['help_test']}")
                print(f"  - {s['help_exit']}\n")
                continue

            if user_input.lower().startswith('/lang '):
                new_lang = user_input.split(' ')[1].strip()
                if new_lang in ['zh', 'en']:
                    lang = new_lang
                    s = UI_STRINGS.get(lang, UI_STRINGS['zh'])
                    print(f"{s['lang_switched']}{lang}")
                    # 同步更新配置中的语言
                    try:
                        with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
                            cfg = json.load(f)
                            cfg['language'] = lang
                            f.seek(0)
                            json.dump(cfg, f, indent=2, ensure_ascii=False)
                            f.truncate()
                    except: pass
                else:
                    print(s['lang_unsupported'])
                continue

            if user_input.lower().startswith('/set-key '):
                new_key = user_input.split(' ', 1)[1].strip()
                try:
                    with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
                        cfg = json.load(f)
                        cfg['apiKey'] = new_key
                        f.seek(0)
                        json.dump(cfg, f, indent=2, ensure_ascii=False)
                        f.truncate()
                    print(s['key_updated'])
                    # 重启守护进程以加载新配置
                    health_url = DAEMON_URL.replace('/command', '/health')
                    try: requests.get(health_url, timeout=0.1) # 触发可能存在的守护进程更新，或在此简单提示
                    except: pass
                except Exception as e:
                    print(f"❌ Error: {e}")
                continue

            if user_input.lower().startswith('/set-url '):
                new_url = user_input.split(' ', 1)[1].strip()
                try:
                    with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
                        cfg = json.load(f)
                        cfg['url'] = new_url
                        f.seek(0)
                        json.dump(cfg, f, indent=2, ensure_ascii=False)
                        f.truncate()
                    print(s['url_updated'])
                except Exception as e:
                    print(f"❌ Error: {e}")
                continue

            if user_input.lower() == '/configure':
                configure_mode(lang)
                continue

            if user_input.lower() == '/testrun':
                print(s['test_start'])
                aps_call(None, lang, is_test=True)
                continue

            # 执行指令
            aps_call(user_input, lang, raw=False)
            print("-" * 30)

        except KeyboardInterrupt:
            print(f"\n{s['exit_msg']}")
            break
        except Exception as e:
            print(f"{s['error_msg']}{e}")

def configure_mode(lang='zh'):
    """交互式配置模式"""
    s = UI_STRINGS.get(lang, UI_STRINGS['zh'])
    print(f"\n{s['config_start']}")
    
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except: pass

    def get_input(prompt, key, default=''):
        val = input(f"{prompt} [{cfg.get(key, default)}]: ").strip()
        return val if val else cfg.get(key, default)

    try:
        cfg['url'] = get_input("Backend URL", 'url', 'http://localhost:3000')
        cfg['apiKey'] = get_input("API KEY", 'apiKey', '')
        cfg['language'] = get_input("Default Language (zh/en)", 'language', 'zh')
        
        ssl_input = input(f"Verify SSL (y/n) [{'y' if cfg.get('verify_ssl', True) else 'n'}]: ").lower().strip()
        if ssl_input:
            cfg['verify_ssl'] = (ssl_input == 'y')
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        
        print(s['config_done'])
    except KeyboardInterrupt:
        print("\n❌ 配置已取消。")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # 加载配置以获取默认语言
    config = {}
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
    except:
        pass
    
    default_lang = config.get('language', 'zh')

    parser = argparse.ArgumentParser(description="Vehicle APS Skill Tool (Resident Service Support)")
    parser.add_argument("command", nargs="?", help="要执行的自然语言指令 (如果不填则进入交互模式)")
    parser.add_argument("lang", nargs="?", default=default_lang, help=f"语言代码 (zh/en, 默认: {default_lang})")
    parser.add_argument("--test", action="store_true", help="运行连接测试模式")
    parser.add_argument("--raw", action="store_true", help="输出原始 JSON 数据")
    parser.add_argument("--status", action="store_true", help="检查常驻服务运行状态")
    parser.add_argument("--set-key", help="更新配置文件中的 API KEY")
    parser.add_argument("--set-url", help="更新配置文件中的后端 URL 地址")
    parser.add_argument("--configure", action="store_true", help="交互式配置系统参数")
    parser.add_argument("--testrun", action="store_true", help="测试连接并自动初始化常驻服务")

    args = parser.parse_args()

    # 处理特定的管理指令 (start, stop, restart, status)
    if args.command in ['start', 'stop', 'restart', 'status']:
        cmd = args.command
        if cmd == 'status':
            check_status()
        elif cmd == 'start':
            if check_status(silent=True):
                print("ℹ️  服务已经在运行中。")
            else:
                print("🕒 正在启动 Vehicle APS 常驻服务...")
                start_daemon()
                print("✅ 服务启动指令已发送。")
        elif cmd == 'stop':
            stop_daemon()
        elif cmd == 'restart':
            print("🔄 正在重启 Vehicle APS 常驻服务...")
            stop_daemon()
            time.sleep(1)
            start_daemon()
            print("✅ 服务重启指令已发送。")
        sys.exit(0)

    if args.status:
        check_status()
        sys.exit(0)

    if args.set_key:
        try:
            with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
                cfg = json.load(f)
                cfg['apiKey'] = args.set_key
                f.seek(0)
                json.dump(cfg, f, indent=2, ensure_ascii=False)
                f.truncate()
            print("✅ API KEY 已成功更新。")
        except Exception as e:
            print(f"❌ Error: {e}")
        sys.exit(0)

    if args.set_url:
        try:
            with open(CONFIG_PATH, 'r+', encoding='utf-8') as f:
                cfg = json.load(f)
                cfg['url'] = args.set_url
                f.seek(0)
                json.dump(cfg, f, indent=2, ensure_ascii=False)
                f.truncate()
            print("✅ URL 地址已成功更新。")
        except Exception as e:
            print(f"❌ Error: {e}")
        sys.exit(0)

    if args.testrun:
        # 直接走测试逻辑，成功后逻辑内会尝试 call_via_daemon -> start_daemon
        aps_call(None, args.lang, is_test=True, raw=args.raw)
        sys.exit(0)

    if args.configure:
        configure_mode(args.lang)
        sys.exit(0)

    if args.test:
        aps_call(None, args.lang, is_test=True, raw=args.raw)
    elif not args.command:
        # 进入交互模式
        interactive_mode(args.lang)
    else:
        aps_call(args.command, args.lang, raw=args.raw)
