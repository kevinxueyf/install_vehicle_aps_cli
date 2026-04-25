import requests
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# 获取脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# =================================================================
# [重型资源加载区]
# 如果您有机器学习模型或大数据集需要加载，请放在这里。
# 这样它们只会在服务启动时加载一次，常驻内存。
# =================================================================
print("🔄 正在加载模型和数据...")
# example_model = load_my_model() 
time.sleep(0.5) # 模拟加载耗时
print("✅ 资源加载完成。")

class APSDaemon:
    def __init__(self):
        self.config = self.load_config()
        self.session = requests.Session()
        self.token = None
        self.base_url = self.config.get('url', '').rstrip('/')
        if self.base_url.endswith('/api'):
            self.base_url = self.base_url[:-4]
        
        self.verify_ssl = self.config.get('verify_ssl', True)
        if not self.verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            print(f"Error: 配置文件未找到：{CONFIG_PATH}")
            sys.exit(1)
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def login(self):
        print("🔑 正在登录以获取新 Token...")
        login_url = f"{self.base_url}/api/auth/login"
        payload = {
            "id": self.config.get('username'),
            "password": self.config.get('password')
        }
        try:
            res = self.session.post(login_url, json=payload, timeout=10, verify=self.verify_ssl)
            data = res.json()
            if data.get('success'):
                self.token = data.get('token')
                print("✅ 登录成功。")
                return True
            else:
                print(f"❌ 登录失败: {data.get('message')}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False

    def call_command(self, command, lang='zh'):
        agent_url = f"{self.base_url}/api/agent/command"
        headers = {}
        api_key = self.config.get('apiKey')

        # 1. 优先使用 API KEY
        if api_key:
            headers["x-api-key"] = api_key
        else:
            # 2. 回退到 Token (密码登录)
            if not self.token:
                if not self.login():
                    return {"success": False, "message": "身份验证失败 (密码登录失败且无 API KEY)"}
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {"command": command, "lang": lang}

        try:
            res = self.session.post(agent_url, json=payload, headers=headers, timeout=30, verify=self.verify_ssl)
            
            # 如果使用 Token 且过期，尝试重新登录一次
            if res.status_code == 401 and not api_key:
                print("⚠️ Token 已过期，尝试重新登录...")
                if self.login():
                    headers["Authorization"] = f"Bearer {self.token}"
                    res = self.session.post(agent_url, json=payload, headers=headers, timeout=30, verify=self.verify_ssl)
                else:
                    return {"success": False, "message": "Token 过期且重新登录失败"}
            
            if res.status_code == 401 and api_key:
                return {"success": False, "message": "API KEY 无效或已失效"}

            return res.json()
        except Exception as e:
            return {"success": False, "message": f"接口调用异常: {str(e)}"}

daemon_instance = None

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 减少日志输出，或者重定向到 stdout
        pass

    def do_POST(self):
        if self.path == '/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            
            command = params.get('command')
            lang = params.get('lang', 'zh')
            
            print(f"🚀 收到指令: {command}")
            result = daemon_instance.call_command(command, lang)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        elif self.path == '/shutdown':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Shutting down...")
            print("\n👋 收到关机指令，正在停止服务...")
            # 在另一个线程中执行，以免阻塞响应
            Thread(target=self.server.shutdown).start()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=5005):
    global daemon_instance
    daemon_instance = APSDaemon()
    server_address = ('127.0.0.1', port)
    
    # 使用 ThreadingHTTPServer 以支持并发请求（如在处理指令时响应健康检查）
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    
    print(f"🚀 Vehicle APS Daemon 已启动，监听端口: {port}")
    print(f"💡 提示: 请保持此窗口运行，或在后台运行此脚本。")
    httpd.serve_forever()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Vehicle APS Resident Daemon")
    parser.add_argument("--port", type=int, default=5005, help="监听端口 (默认 5005)")
    args = parser.parse_args()
    
    try:
        run_server(args.port)
    except KeyboardInterrupt:
        print("\n👋 正在停止服务...")
        sys.exit(0)
