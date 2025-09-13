"""Google Services认证命令 - Sprint 9-10核心功能"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional, List
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from pm.core.config import PMConfig
from pm.integrations.google_auth import GoogleAuthManager

console = Console()

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
            
            print(f"[DEBUG] 收到回调URL: {callback_url}")
            
            # 处理认证回调 - 使用全局实例确保状态参数一致
            if _global_google_auth is not None:
                success, message = _global_google_auth.handle_google_callback(callback_url)
            else:
                # 备用方案：创建新实例
                config = PMConfig()
                google_auth = GoogleAuthManager(config)
                success, message = google_auth.handle_google_callback(callback_url)
            
            print(f"[DEBUG] 认证结果: success={success}, message={message}")
            
            # 存储结果供主线程使用
            OAuthCallbackHandler.callback_result = (success, message)
            
            # 返回响应页面
            if success:
                response_html = """
                <html>
                <head><title>认证成功</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ 认证成功！</h1>
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


def start_callback_server() -> HTTPServer:
    """启动OAuth回调服务器"""
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    return server


# 全局GoogleAuthManager实例，确保状态参数一致
_global_google_auth = None

def google_auth_login(services: Optional[List[str]] = None) -> None:
    """Google服务登录认证"""
    global _global_google_auth
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    # 使用全局实例确保状态参数一致性
    _global_google_auth = GoogleAuthManager(config)
    google_auth = _global_google_auth
    
    # 检查凭证是否已配置
    if not google_auth.is_credentials_configured():
        console.print(Panel(
            "[red]Google OAuth凭证未配置[/red]\\n\\n"
            "请确保已将Google OAuth凭证文件放置在：\\n"
            "[cyan]~/.personalmanager/credentials.json[/cyan]\\n\\n"
            "凭证文件应包含以下格式：\\n"
            "[dim]{\\n"
            '  "web": {\\n'
            '    "client_id": "your-client-id",\\n'
            '    "client_secret": "your-client-secret"\\n'
            "  }\\n"
            "}[/dim]\\n\\n"
            "或简化格式：\\n"
            "[dim]{\\n"
            '  "client_id": "your-client-id",\\n'
            '  "client_secret": "your-client-secret"\\n'
            "}[/dim]",
            title="❌ 凭证配置错误",
            border_style="red"
        ))
        return
    
    # 检查是否已经认证
    if google_auth.is_google_authenticated():
        console.print(Panel(
            "[green]您已经通过Google服务认证。\\n\\n"
            "如需重新认证，请先运行：[cyan]pm auth logout google[/cyan]",
            title="✅ 已认证",
            border_style="green"
        ))
        return
    
    # 显示认证信息
    console.print(Panel(
        "[cyan]🔐 Google Services 认证[/cyan]\\n\\n"
        "即将为以下服务进行认证：\\n"
        f"• [yellow]Google Calendar[/yellow] - 日程管理\\n"
        f"• [yellow]Google Tasks[/yellow] - 任务同步\\n" 
        f"• [yellow]Google Gmail[/yellow] - 重要邮件识别\\n\\n"
        "[dim]认证过程中会打开浏览器页面，请按提示完成授权。[/dim]",
        title="📋 认证说明",
        border_style="blue"
    ))
    
    # 用户确认
    if not typer.confirm("继续进行Google认证？"):
        console.print("[yellow]认证已取消。[/yellow]")
        return
    
    try:
        # 启动回调服务器
        console.print("[dim]启动本地回调服务器...[/dim]")
        server = start_callback_server()
        
        # 在后台线程中运行服务器
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # 生成认证URL并打开浏览器
        auth_url, state = google_auth.start_google_auth(services)
        
        console.print("\\n[green]正在打开浏览器进行认证...[/green]")
        google_auth.open_auth_url_in_browser(auth_url)
        
        console.print(Panel(
            f"[yellow]如浏览器未自动打开，请手动访问：[/yellow]\\n"
            f"[cyan]{auth_url}[/cyan]\\n\\n"
            f"[dim]等待认证回调...[/dim]",
            title="🌐 浏览器认证",
            border_style="yellow"
        ))
        
        # 等待认证回调
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("等待用户完成认证...", total=None)
            
            # 轮询等待回调结果
            timeout = 300  # 5分钟超时
            start_time = time.time()
            
            while OAuthCallbackHandler.callback_result is None:
                if time.time() - start_time > timeout:
                    progress.update(task, description="[red]认证超时")
                    break
                time.sleep(1)
        
        # 关闭服务器
        server.shutdown()
        server.server_close()
        
        # 处理认证结果
        if OAuthCallbackHandler.callback_result:
            success, message = OAuthCallbackHandler.callback_result
            if success:
                console.print(Panel(
                    f"[green]✅ {message}[/green]\\n\\n"
                    "现在您可以使用Google服务集成功能：\\n"
                    "• [cyan]pm calendar sync[/cyan] - 同步日程\\n"
                    "• [cyan]pm tasks sync[/cyan] - 同步任务\\n"
                    "• [cyan]pm gmail check[/cyan] - 检查重要邮件",
                    title="🎉 认证成功",
                    border_style="green"
                ))
            else:
                console.print(Panel(
                    f"[red]❌ {message}[/red]",
                    title="认证失败",
                    border_style="red"
                ))
        else:
            console.print(Panel(
                "[red]❌ 认证超时或用户取消[/red]\\n\\n"
                "请重新运行命令进行认证。",
                title="认证失败",
                border_style="red"
            ))
    
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 认证过程中发生错误: {str(e)}[/red]",
            title="认证错误",
            border_style="red"
        ))


def google_auth_logout() -> None:
    """Google服务登出"""
    
    config = PMConfig()
    google_auth = GoogleAuthManager(config)
    
    if not google_auth.is_google_authenticated():
        console.print(Panel(
            "[yellow]您尚未通过Google服务认证。[/yellow]",
            title="⚠️ 未认证",
            border_style="yellow"
        ))
        return
    
    # 用户确认
    if not typer.confirm("确定要登出Google服务认证吗？这会撤销所有Google服务的访问权限。"):
        console.print("[yellow]登出已取消。[/yellow]")
        return
    
    try:
        success = google_auth.revoke_google_auth()
        
        if success:
            console.print(Panel(
                "[green]✅ 已成功登出Google服务[/green]\\n\\n"
                "所有Google服务的访问权限已被撤销。\\n"
                "如需重新使用，请运行：[cyan]pm auth login google[/cyan]",
                title="🚪 登出成功",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]❌ 登出失败[/red]\\n\\n"
                "请检查网络连接或重试。",
                title="登出失败",
                border_style="red"
            ))
    
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 登出过程中发生错误: {str(e)}[/red]",
            title="登出错误",
            border_style="red"
        ))


def show_auth_status() -> None:
    """显示认证状态"""
    
    config = PMConfig()
    google_auth = GoogleAuthManager(config)
    
    # 获取认证状态
    auth_status = google_auth.get_google_auth_status()
    
    # 创建状态表格
    status_table = Table(show_header=True, header_style="bold magenta")
    status_table.add_column("服务", style="cyan")
    status_table.add_column("认证状态", style="green", justify="center")
    status_table.add_column("详细信息", style="yellow")
    
    if auth_status['authenticated']:
        status_emoji = "✅"
        status_text = "已认证"
        status_style = "green"
        details = f"过期时间: {auth_status.get('expires_at', 'N/A')}"
    else:
        status_emoji = "❌"
        status_text = "未认证"
        status_style = "red"
        details = auth_status.get('message', '未知状态')
    
    status_table.add_row(
        "Google Services",
        f"[{status_style}]{status_emoji} {status_text}[/{status_style}]",
        details
    )
    
    # 显示状态面板
    console.print(Panel(
        status_table,
        title="🔐 认证状态",
        border_style="blue"
    ))
    
    # 显示可用命令
    if auth_status['authenticated']:
        console.print(Panel(
            "[green]✅ Google服务已认证[/green]\\n\\n"
            "可用命令：\\n"
            "• [cyan]pm calendar sync[/cyan] - 同步Google Calendar\\n"
            "• [cyan]pm tasks sync[/cyan] - 同步Google Tasks\\n"
            "• [cyan]pm gmail check[/cyan] - 检查重要邮件\\n"
            "• [cyan]pm auth logout google[/cyan] - 登出认证",
            title="📋 可用功能",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[yellow]⚠️ 需要认证Google服务[/yellow]\\n\\n"
            "请运行以下命令进行认证：\\n"
            "[cyan]pm auth login google[/cyan]",
            title="🔑 认证提示",
            border_style="yellow"
        ))