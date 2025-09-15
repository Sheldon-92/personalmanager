#!/usr/bin/env python3
"""
Personal账号认证脚本
"""

import sys
import os
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.core.config import PMConfig
from pm.integrations.google_auth import GoogleAuthManager

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调的HTTP服务器"""

    callback_result = None

    def do_GET(self):
        """处理GET请求（OAuth回调）"""

        # 解析URL和参数
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == '/oauth/callback':
            # 这是OAuth回调
            callback_url = f"http://localhost:8080{self.path}"

            print(f"\n收到回调URL: {callback_url}")

            # 处理认证回调
            config = PMConfig()
            google_auth = GoogleAuthManager(config)
            success, message = google_auth.handle_google_callback(callback_url)

            print(f"认证结果: success={success}, message={message}")

            # 存储结果供主线程使用
            OAuthCallbackHandler.callback_result = (success, message)

            # 返回响应页面
            if success:
                response_html = """
                <html>
                <head><title>认证成功</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Personal账号认证成功！</h1>
                    <p>您已成功通过Google服务认证。</p>
                    <p>现在可以关闭此页面，返回命令行继续操作。</p>
                </body>
                </html>
                """
            else:
                response_html = f"""
                <html>
                <head><title>认证失败</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ 认证失败</h1>
                    <p>{message}</p>
                    <p>请关闭此页面，返回命令行重试。</p>
                </body>
                </html>
                """

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(response_html.encode('utf-8'))
        else:
            # 404响应
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>404 Not Found</h1></body></html>')

    def log_message(self, format, *args):
        """禁用HTTP服务器的日志输出"""
        pass


def main():
    """主函数"""

    print("🔐 Personal Google账号认证")
    print("=" * 40)

    config = PMConfig()
    google_auth = GoogleAuthManager(config)

    # 检查凭证
    if not google_auth.is_account_credentials_configured('personal'):
        print("❌ Personal账号凭证未配置")
        print("请确保 ~/.personalmanager/credentials_personal.json 文件存在")
        return

    print("✅ Personal账号凭证已配置")

    # 检查是否已认证
    if google_auth.is_google_authenticated('personal'):
        print("✅ Personal账号已认证，无需重新认证")
        return

    try:
        # 启动回调服务器
        print("🚀 启动本地回调服务器...")
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)

        # 在后台线程中运行服务器
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # 生成认证URL
        auth_url, state = google_auth.start_google_auth(account_alias='personal')

        print("🌐 正在打开浏览器进行认证...")
        print(f"如浏览器未自动打开，请手动访问：")
        print(f"{auth_url}")

        # 打开浏览器
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")

        print("\n⏳ 等待用户完成认证...")
        print("请在浏览器中使用您的常用Google账号登录并完成授权")

        # 等待认证回调
        timeout = 300  # 5分钟超时
        start_time = time.time()

        while OAuthCallbackHandler.callback_result is None:
            if time.time() - start_time > timeout:
                print("⏰ 认证超时")
                break
            time.sleep(1)

        # 关闭服务器
        server.shutdown()
        server.server_close()

        # 处理认证结果
        if OAuthCallbackHandler.callback_result:
            success, message = OAuthCallbackHandler.callback_result
            if success:
                print("🎉 认证成功！")
                print(f"✅ {message}")
                print("\n现在您可以使用以下命令:")
                print("• pm calendar sync --account=personal")
                print("• pm auth switch-default personal")
            else:
                print("❌ 认证失败")
                print(f"错误: {message}")
        else:
            print("❌ 认证超时或用户取消")

    except Exception as e:
        print(f"❌ 认证过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()