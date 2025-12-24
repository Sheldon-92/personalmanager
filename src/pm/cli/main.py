#!/usr/bin/env python3
"""PersonalManager CLI - 极简版

只包含5个核心命令：
- pm today   : 今日日程和任务
- pm inbox   : 待处理任务
- pm sync    : 同步 Google Calendar/Tasks
- pm add     : 快速添加任务
- pm cal     : 查看日历
"""

import typer
from typing import Optional
from datetime import datetime, date, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

app = typer.Typer(
    name="pm",
    help="PersonalManager - 极简个人任务管理",
    no_args_is_help=True,
)
console = Console()


def get_config():
    """延迟加载配置"""
    from pm.core.config import PMConfig
    return PMConfig()


def get_google_tasks():
    """延迟加载 Google Tasks 管理器"""
    from pm.integrations.google_tasks import GoogleTasksIntegration
    config = get_config()
    return GoogleTasksIntegration(config)


def get_google_calendar():
    """延迟加载 Google Calendar 管理器"""
    from pm.integrations.google_calendar import GoogleCalendarIntegration
    config = get_config()
    return GoogleCalendarIntegration(config)


def is_task_today(task) -> bool:
    """检查任务是否在今天截止"""
    if task.due is None:
        return False
    task_date = task.due.date() if hasattr(task.due, 'date') else task.due
    return task_date == date.today()


@app.command()
def today():
    """查看今日日程和任务"""
    console.print(Panel.fit(
        f"[bold cyan]今日概览[/bold cyan] - {date.today().strftime('%Y-%m-%d %A')}",
        border_style="cyan"
    ))

    try:
        # 获取今日任务
        tasks_manager = get_google_tasks()
        google_tasks = tasks_manager._fetch_google_tasks()
        today_tasks = [t for t in google_tasks if is_task_today(t) and not t.is_completed]

        if today_tasks:
            table = Table(title="今日任务", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("任务", style="white")
            table.add_column("状态", style="green", width=8)

            for i, task in enumerate(today_tasks, 1):
                status = "✅" if task.is_completed else "⬜"
                table.add_row(str(i), task.title, status)

            console.print(table)
        else:
            console.print("[dim]今日暂无任务[/dim]")

        # 获取今日日程
        cal_manager = get_google_calendar()
        events = cal_manager.get_today_schedule()

        if events:
            console.print()
            table = Table(title="今日日程", show_header=True, header_style="bold blue")
            table.add_column("时间", style="cyan", width=12)
            table.add_column("事件", style="white")

            for event in events:
                time_str = event.start_time.strftime("%H:%M") if event.start_time else "全天"
                table.add_row(time_str, event.title)

            console.print(table)
        else:
            console.print("[dim]今日暂无日程[/dim]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("[dim]提示: 请先运行 'pm sync' 确保已登录 Google 账户[/dim]")


@app.command()
def inbox():
    """查看待处理任务（收件箱）"""
    console.print(Panel.fit("[bold yellow]收件箱[/bold yellow]", border_style="yellow"))

    try:
        tasks_manager = get_google_tasks()
        google_tasks = tasks_manager._fetch_google_tasks()
        # 过滤未完成的任务
        pending_tasks = [t for t in google_tasks if not t.is_completed]

        if pending_tasks:
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=3)
            table.add_column("任务", style="white")
            table.add_column("截止日期", style="cyan", width=12)

            for i, task in enumerate(pending_tasks, 1):
                due = task.due.strftime("%Y-%m-%d") if task.due else "-"
                table.add_row(str(i), task.title, due)

            console.print(table)
            console.print(f"\n[dim]共 {len(pending_tasks)} 个待处理任务[/dim]")
        else:
            console.print("[green]收件箱为空，太棒了！[/green]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


# OAuth 回调处理器
_global_google_auth = None
_callback_result = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调的HTTP服务器"""

    def do_GET(self):
        global _callback_result, _global_google_auth
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == '/oauth/callback':
            callback_url = f"http://localhost:8080{self.path}"

            if _global_google_auth is not None:
                success, message = _global_google_auth.handle_google_callback(callback_url)
            else:
                config = get_config()
                from pm.integrations.google_auth import GoogleAuthManager
                google_auth = GoogleAuthManager(config)
                success, message = google_auth.handle_google_callback(callback_url)

            _callback_result = (success, message)

            if success:
                response_html = """
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ 认证成功！</h1>
                    <p>现在可以关闭此页面，返回命令行继续操作。</p>
                </body></html>
                """
            else:
                response_html = f"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ 认证失败</h1>
                    <p>{message}</p>
                </body></html>
                """

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(response_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 禁用日志


def do_google_auth(auth) -> bool:
    """执行 Google OAuth 认证流程"""
    global _global_google_auth, _callback_result
    _global_google_auth = auth
    _callback_result = None

    try:
        # 启动回调服务器
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # 生成认证URL并打开浏览器
        auth_url, state = auth.start_google_auth()
        console.print("\n[green]正在打开浏览器进行认证...[/green]")
        auth.open_auth_url_in_browser(auth_url)

        console.print(Panel(
            f"[yellow]如浏览器未自动打开，请手动访问：[/yellow]\n[cyan]{auth_url}[/cyan]",
            title="🌐 浏览器认证",
            border_style="yellow"
        ))

        # 等待认证回调
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("等待用户完成认证...", total=None)

            timeout = 300  # 5分钟超时
            start_time = time.time()

            while _callback_result is None:
                if time.time() - start_time > timeout:
                    break
                time.sleep(1)

        server.shutdown()
        server.server_close()

        if _callback_result:
            success, message = _callback_result
            return success
        return False

    except Exception as e:
        console.print(f"[red]认证错误: {e}[/red]")
        return False


@app.command()
def sync():
    """验证 Google 连接并刷新认证"""
    console.print(Panel.fit("[bold green]同步 Google 服务[/bold green]", border_style="green"))

    try:
        from pm.integrations.google_auth import GoogleAuthManager
        config = get_config()
        auth = GoogleAuthManager(config)

        # 检查认证状态
        if not auth.is_google_authenticated():
            console.print("[yellow]未登录，正在启动认证流程...[/yellow]")
            if not do_google_auth(auth):
                console.print("[red]认证失败或超时[/red]")
                return
            console.print("[green]✓ 认证成功！[/green]")
        else:
            console.print("[green]✓ 已登录 Google 账户[/green]")

        # 验证 Tasks API 连接
        console.print("\n[cyan]验证 Google Tasks...[/cyan]")
        tasks_manager = get_google_tasks()
        google_tasks = tasks_manager._fetch_google_tasks()
        console.print(f"[green]✓ 已连接 Google Tasks ({len(google_tasks)} 个任务)[/green]")

        # 验证 Calendar API 连接
        console.print("\n[cyan]验证 Google Calendar...[/cyan]")
        cal_manager = get_google_calendar()
        events = cal_manager.get_today_schedule()
        console.print(f"[green]✓ 已连接 Google Calendar ({len(events)} 个今日日程)[/green]")

        console.print("\n[bold green]连接验证完成！[/bold green]")
        console.print("[dim]提示: 使用 'pm today' 查看今日任务和日程[/dim]")

    except Exception as e:
        console.print(f"[red]同步错误: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@app.command()
def add(
    title: str = typer.Argument(..., help="任务标题"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="截止日期 (YYYY-MM-DD)")
):
    """快速添加任务到 Google Tasks"""
    try:
        from pm.models.task import Task, TaskStatus

        tasks_manager = get_google_tasks()

        due_date = None
        if due:
            try:
                due_date = datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                console.print("[red]日期格式错误，请使用 YYYY-MM-DD[/red]")
                return

        # 创建任务对象
        task = Task(
            id=f"local_{datetime.now().timestamp()}",
            title=title,
            status=TaskStatus.PENDING,
            due_date=due_date,
        )

        # 同步到 Google
        success, msg = tasks_manager.sync_task_to_google(task)

        if success:
            console.print(f"[green]✓ 已添加任务: {title}[/green]")
            if due_date:
                console.print(f"[dim]  截止日期: {due_date.strftime('%Y-%m-%d')}[/dim]")
        else:
            console.print(f"[red]添加失败: {msg}[/red]")

    except Exception as e:
        console.print(f"[red]添加失败: {e}[/red]")


@app.command()
def cal(
    days: int = typer.Option(7, "--days", "-d", help="显示未来几天的日程")
):
    """查看日历（默认未来7天）"""
    console.print(Panel.fit(
        f"[bold blue]日历视图[/bold blue] - 未来 {days} 天",
        border_style="blue"
    ))

    try:
        cal_manager = get_google_calendar()
        events = cal_manager.get_upcoming_events(days_ahead=days)

        # 按日期分组
        events_by_date = {}
        for event in events:
            event_date = event.start_time.date() if event.start_time else date.today()
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        for i in range(days):
            target_date = date.today() + timedelta(days=i)
            date_events = events_by_date.get(target_date, [])

            # 日期标题
            date_str = target_date.strftime("%m/%d %a")
            if i == 0:
                date_str += " (今天)"
            elif i == 1:
                date_str += " (明天)"

            if date_events:
                console.print(f"\n[bold cyan]{date_str}[/bold cyan]")
                for event in sorted(date_events, key=lambda e: e.start_time or datetime.min):
                    time_str = event.start_time.strftime("%H:%M") if event.start_time else "全天"
                    console.print(f"  [dim]{time_str}[/dim] {event.title}")
            else:
                console.print(f"\n[dim]{date_str} - 无日程[/dim]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


@app.command()
def next(
    path: str = typer.Option("~/programs", "--path", "-p", help="项目目录路径"),
    push: bool = typer.Option(False, "--push", help="推送任务到 Google Tasks"),
    pull: bool = typer.Option(False, "--pull", help="从 Google Tasks 拉取完成状态")
):
    """查看/同步所有项目的下一步行动"""
    import os

    # Check for mutual exclusivity
    if push and pull:
        console.print("[red]错误: --push 和 --pull 不能同时使用[/red]")
        return

    if push:
        _do_next_push(path)
    elif pull:
        _do_next_pull(path)
    else:
        _do_next_list(path)


def _do_next_push(path: str):
    """Push tasks to Google Tasks"""
    from pm.core.next_sync import NextSyncManager

    console.print(Panel.fit(
        "[bold green]推送任务到 Google Tasks[/bold green]",
        border_style="green"
    ))

    try:
        config = get_config()
        sync_manager = NextSyncManager(config, path)

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("正在同步...", total=None)
            stats = sync_manager.push()

        # Display results
        console.print()
        console.print(f"[cyan]扫描项目:[/cyan] {stats.projects_scanned}")
        console.print(f"[cyan]发现任务:[/cyan] {stats.tasks_found}")
        console.print(f"[green]已推送:[/green] {stats.tasks_pushed}")
        console.print(f"[yellow]已跳过(重复):[/yellow] {stats.tasks_skipped}")

        if stats.errors:
            console.print(f"\n[red]错误 ({len(stats.errors)}):[/red]")
            for err in stats.errors[:5]:  # Show first 5 errors
                console.print(f"  [dim]• {err}[/dim]")

        if stats.tasks_pushed > 0:
            console.print(f"\n[green]✓ 已同步到 Google Tasks 'NEXT Tasks' 列表[/green]")

    except Exception as e:
        console.print(f"[red]推送失败: {e}[/red]")


def _do_next_pull(path: str):
    """Pull completed tasks from Google Tasks"""
    from pm.core.next_sync import NextSyncManager

    console.print(Panel.fit(
        "[bold blue]从 Google Tasks 拉取完成状态[/bold blue]",
        border_style="blue"
    ))

    try:
        config = get_config()
        sync_manager = NextSyncManager(config, path)

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("正在拉取...", total=None)
            stats = sync_manager.pull()

        # Display results
        console.print()
        console.print(f"[cyan]已完成任务:[/cyan] {stats.tasks_pulled}")
        console.print(f"[green]已更新 NEXT.md:[/green] {stats.tasks_updated}")

        if stats.errors:
            console.print(f"\n[red]错误 ({len(stats.errors)}):[/red]")
            for err in stats.errors[:5]:
                console.print(f"  [dim]• {err}[/dim]")

        if stats.tasks_updated > 0:
            console.print(f"\n[green]✓ 已更新各项目 NEXT.md 文件[/green]")

    except Exception as e:
        console.print(f"[red]拉取失败: {e}[/red]")


def _do_next_list(path: str):
    """List tasks from all NEXT.md files (original behavior)"""
    import os

    # 展开路径
    projects_dir = os.path.expanduser(path)

    if not os.path.isdir(projects_dir):
        console.print(f"[red]目录不存在: {projects_dir}[/red]")
        return

    console.print(Panel.fit(
        f"[bold green]跨项目任务汇总[/bold green]",
        border_style="green"
    ))

    all_tasks = []

    # 扫描所有子目录
    for item in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, item)
        next_file = os.path.join(project_path, "NEXT.md")

        if os.path.isdir(project_path) and os.path.isfile(next_file):
            try:
                with open(next_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析 NEXT.md
                current_section = None
                for line in content.split('\n'):
                    line = line.strip()

                    # 检测分类标题
                    if line.startswith('## '):
                        section = line[3:].strip()
                        if '今天' in section or 'today' in section.lower():
                            current_section = '今天'
                        elif '本周' in section or 'week' in section.lower():
                            current_section = '本周'
                        elif '阻塞' in section or 'block' in section.lower():
                            current_section = '阻塞'
                        else:
                            current_section = '待定'

                    # 检测未完成任务
                    elif line.startswith('- [ ]') and current_section:
                        task_text = line[5:].strip()
                        all_tasks.append({
                            'project': item,
                            'task': task_text,
                            'priority': current_section
                        })
            except Exception as e:
                console.print(f"[dim]读取 {item}/NEXT.md 失败: {e}[/dim]")

    if not all_tasks:
        console.print("[dim]没有找到任何项目的 NEXT.md 文件[/dim]")
        console.print(f"[dim]扫描路径: {projects_dir}[/dim]")
        console.print(f"\n[dim]提示: 使用 --push 推送任务到 Google Tasks[/dim]")
        return

    # 按优先级分组显示
    priority_order = ['今天', '本周', '阻塞', '待定']

    for priority in priority_order:
        tasks = [t for t in all_tasks if t['priority'] == priority]
        if tasks:
            # 选择颜色
            color = {'今天': 'red', '本周': 'yellow', '阻塞': 'magenta', '待定': 'dim'}[priority]
            console.print(f"\n[bold {color}]## {priority}[/bold {color}]")

            for t in tasks:
                console.print(f"  [{color}]○[/{color}] [cyan]{t['project']}[/cyan]: {t['task']}")

    console.print(f"\n[dim]共 {len(all_tasks)} 个待办，来自 {len(set(t['project'] for t in all_tasks))} 个项目[/dim]")
    console.print(f"[dim]提示: --push 推送到 Google | --pull 拉取完成状态[/dim]")


@app.command()
def version():
    """显示版本信息"""
    console.print("[bold]PersonalManager[/bold] v2.0.0 (极简版)")
    console.print("[dim]管理你的日程、任务和项目进展[/dim]")


def main():
    """入口函数"""
    app()


if __name__ == "__main__":
    main()
