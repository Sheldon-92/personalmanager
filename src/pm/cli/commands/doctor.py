"""系统环境与权限自检命令 - pm doctor

诊断PersonalManager运行环境，检查关键配置和依赖项
"""

import os
import sys
import shutil
import platform
import subprocess
import socket
import ssl
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.columns import Columns

from pm.core.config import PMConfig

console = Console()
doctor_app = typer.Typer(name="doctor", help="系统环境与权限自检诊断")

class SystemCheck:
    """系统检查项"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = "PENDING"
        self.details = ""
        self.fix_suggestion = ""
    
    def pass_check(self, details: str = ""):
        self.status = "PASS"
        self.details = details
    
    def fail_check(self, details: str = "", fix_suggestion: str = ""):
        self.status = "FAIL"
        self.details = details
        self.fix_suggestion = fix_suggestion
    
    def skip_check(self, reason: str = ""):
        self.status = "SKIP"
        self.details = reason

class PMDoctor:
    """PersonalManager系统诊断器"""

    def __init__(self):
        self.config = None
        self.checks: List[SystemCheck] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.platform_info = self._detect_platform()
        self.network_available = self._check_network()

    def _detect_platform(self) -> Dict[str, str]:
        """检测平台信息"""
        try:
            system = platform.system().lower()
            if system == "linux" and "microsoft" in platform.release().lower():
                system = "wsl"

            return {
                "system": system,
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0]
            }
        except Exception:
            return {"system": "unknown"}

    def _check_network(self) -> bool:
        """检测网络连接"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (OSError, socket.timeout):
            return False
    
    def add_check(self, check: SystemCheck) -> SystemCheck:
        """添加检查项"""
        self.checks.append(check)
        return check
    
    def check_python_version(self) -> SystemCheck:
        """检查Python版本 >= 3.9"""
        check = self.add_check(SystemCheck(
            "Python版本", 
            "验证Python版本是否满足最低要求(>=3.9)"
        ))
        
        try:
            version = sys.version_info
            current_version = f"{version.major}.{version.minor}.{version.micro}"
            
            if version.major == 3 and version.minor >= 9:
                check.pass_check(f"Python {current_version} ✓")
            else:
                check.fail_check(
                    f"Python {current_version} (需要 >= 3.9)",
                    "请升级Python到3.9或更高版本: https://python.org"
                )
        except Exception as e:
            check.fail_check(f"无法检测Python版本: {e}")
        
        return check
    
    def check_config_initialization(self) -> SystemCheck:
        """检查配置文件初始化状态"""
        check = self.add_check(SystemCheck(
            "配置初始化", 
            "验证PersonalManager是否已正确初始化"
        ))
        
        try:
            self.config = PMConfig()
            if self.config.is_initialized():
                check.pass_check(f"配置文件存在: {self.config.config_file}")
            else:
                check.fail_check(
                    "配置未初始化",
                    "运行 'pm setup' 初始化系统配置"
                )
        except Exception as e:
            check.fail_check(f"配置检查失败: {e}", "请检查配置文件完整性")
        
        return check
    
    def check_data_directories(self) -> SystemCheck:
        """检查数据目录权限和存在性"""
        check = self.add_check(SystemCheck(
            "数据目录", 
            "验证数据目录是否存在且可写"
        ))
        
        try:
            if not self.config:
                check.skip_check("配置未初始化")
                return check
            
            data_dir = self.config.data_dir
            if not data_dir.exists():
                check.fail_check(
                    f"数据目录不存在: {data_dir}",
                    "运行 'pm setup' 创建必要目录"
                )
                return check
            
            # 检查写权限
            test_file = data_dir / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                check.pass_check(f"数据目录可写: {data_dir}")
            except Exception:
                check.fail_check(
                    f"数据目录无写权限: {data_dir}",
                    f"检查目录权限: chmod 755 {data_dir}"
                )
                
        except Exception as e:
            check.fail_check(f"目录检查失败: {e}")
        
        return check
    
    def check_tokens_directory(self) -> SystemCheck:
        """检查tokens目录存在性"""
        check = self.add_check(SystemCheck(
            "Tokens目录", 
            "验证API凭证存储目录是否存在"
        ))
        
        try:
            if not self.config:
                check.skip_check("配置未初始化")
                return check
            
            tokens_dir = self.config.data_dir / "tokens"
            if tokens_dir.exists():
                check.pass_check(f"Tokens目录存在: {tokens_dir}")
            else:
                check.fail_check(
                    f"Tokens目录不存在: {tokens_dir}",
                    f"创建目录: mkdir -p {tokens_dir}"
                )
                
        except Exception as e:
            check.fail_check(f"Tokens目录检查失败: {e}")
        
        return check
    
    def check_disk_space(self) -> SystemCheck:
        """检查磁盘可用空间"""
        check = self.add_check(SystemCheck(
            "磁盘空间", 
            "验证可用磁盘空间是否充足(>200MB)"
        ))
        
        try:
            if not self.config:
                check.skip_check("配置未初始化")
                return check
            
            # 获取数据目录所在磁盘的可用空间
            statvfs = os.statvfs(self.config.data_dir)
            available_bytes = statvfs.f_bavail * statvfs.f_frsize
            available_mb = available_bytes / (1024 * 1024)
            
            threshold_mb = 200
            if available_mb > threshold_mb:
                check.pass_check(f"可用空间: {available_mb:.1f}MB")
            else:
                check.fail_check(
                    f"可用空间不足: {available_mb:.1f}MB (需要 > {threshold_mb}MB)",
                    "清理磁盘空间或选择其他存储位置"
                )
                
        except Exception as e:
            check.fail_check(f"磁盘空间检查失败: {e}")
        
        return check
    
    def check_required_directories(self) -> SystemCheck:
        """检查必要的子目录结构"""
        check = self.add_check(SystemCheck(
            "目录结构", 
            "验证必要的子目录是否存在"
        ))
        
        try:
            if not self.config:
                check.skip_check("配置未初始化")
                return check
            
            required_dirs = [
                "tasks", "habits", "projects", "logs", 
                "backups", "tokens"
            ]
            
            missing_dirs = []
            existing_dirs = []
            
            for dir_name in required_dirs:
                dir_path = self.config.data_dir / dir_name
                if dir_path.exists():
                    existing_dirs.append(dir_name)
                else:
                    missing_dirs.append(dir_name)
            
            if not missing_dirs:
                check.pass_check(f"所有目录存在: {', '.join(existing_dirs)}")
            else:
                check.fail_check(
                    f"缺少目录: {', '.join(missing_dirs)}",
                    f"创建缺少的目录或运行 'pm setup'"
                )
                
        except Exception as e:
            check.fail_check(f"目录结构检查失败: {e}")
        
        return check
    
    def check_system_commands(self) -> SystemCheck:
        """检查系统必要命令"""
        check = self.add_check(SystemCheck(
            "系统命令",
            "验证必要的系统命令是否可用"
        ))

        try:
            # 平台特定的必要命令
            commands = {
                "common": ["git", "curl"],
                "macos": ["brew"],
                "linux": ["apt", "yum", "dnf"],
                "wsl": ["apt"]
            }

            # 检查通用命令
            required = commands["common"]
            if self.platform_info["system"] in commands:
                # 添加平台特定命令（至少一个可用即可）
                platform_cmds = commands[self.platform_info["system"]]
                required.extend(platform_cmds)

            available_commands = []
            missing_commands = []

            for cmd in commands["common"]:
                if shutil.which(cmd):
                    available_commands.append(cmd)
                else:
                    missing_commands.append(cmd)

            # 对于平台特定命令，只需要有一个可用
            if self.platform_info["system"] in commands:
                platform_cmds = commands[self.platform_info["system"]]
                has_package_manager = any(shutil.which(cmd) for cmd in platform_cmds)
                if has_package_manager:
                    available_commands.extend([cmd for cmd in platform_cmds if shutil.which(cmd)])
                else:
                    missing_commands.extend(platform_cmds)

            if not missing_commands:
                check.pass_check(f"命令可用: {', '.join(available_commands)}")
            else:
                suggestions = self._get_install_suggestions(missing_commands)
                check.fail_check(
                    f"缺少命令: {', '.join(missing_commands)}",
                    suggestions
                )

        except Exception as e:
            check.fail_check(f"命令检查失败: {e}")

        return check

    def _get_install_suggestions(self, missing_commands: List[str]) -> str:
        """获取安装建议"""
        system = self.platform_info["system"]
        suggestions = []

        for cmd in missing_commands:
            if cmd == "git":
                if system == "macos":
                    suggestions.append("Git: xcode-select --install 或 brew install git")
                elif system in ["linux", "wsl"]:
                    suggestions.append("Git: sudo apt install git")
                else:
                    suggestions.append("Git: https://git-scm.com/downloads")
            elif cmd == "curl":
                if system == "macos":
                    suggestions.append("Curl: 通常已预装，或 brew install curl")
                elif system in ["linux", "wsl"]:
                    suggestions.append("Curl: sudo apt install curl")
            elif cmd == "brew":
                suggestions.append("Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")

        return "; ".join(suggestions) if suggestions else "请查阅系统文档安装缺少的命令"
    
    def check_permissions(self) -> SystemCheck:
        """检查关键目录的权限"""
        check = self.add_check(SystemCheck(
            "文件权限", 
            "验证关键文件和目录的权限设置"
        ))
        
        try:
            if not self.config:
                check.skip_check("配置未初始化")
                return check
            
            # 检查配置文件权限
            config_file = self.config.config_file
            if config_file.exists():
                # 检查是否可读
                if os.access(config_file, os.R_OK):
                    check.pass_check("配置文件权限正常")
                else:
                    check.fail_check(
                        "配置文件无读权限",
                        f"修复权限: chmod 644 {config_file}"
                    )
            else:
                check.fail_check("配置文件不存在")
                
        except Exception as e:
            check.fail_check(f"权限检查失败: {e}")

        return check

    def check_environment_variables(self) -> SystemCheck:
        """检查环境变量"""
        check = self.add_check(SystemCheck(
            "环境变量",
            "验证重要的环境变量设置"
        ))

        try:
            important_vars = {
                "HOME": "用户主目录",
                "PATH": "系统路径",
                "LANG": "系统语言",
                "SHELL": "默认Shell"
            }

            missing_vars = []
            present_vars = []

            for var, desc in important_vars.items():
                if os.getenv(var):
                    present_vars.append(f"{var}({desc})")
                else:
                    missing_vars.append(f"{var}({desc})")

            if not missing_vars:
                check.pass_check(f"环境变量完整: {len(present_vars)}个")
            else:
                check.fail_check(
                    f"缺少环境变量: {', '.join(missing_vars)}",
                    "检查Shell配置文件(.bashrc, .zshrc等)"
                )

        except Exception as e:
            check.fail_check(f"环境变量检查失败: {e}")

        return check

    def check_python_modules(self) -> SystemCheck:
        """检查Python模块依赖"""
        check = self.add_check(SystemCheck(
            "Python模块",
            "验证关键Python依赖模块"
        ))

        try:
            required_modules = [
                "typer", "rich", "pydantic", "watchdog",
                "structlog", "yaml", "pathlib"
            ]

            available_modules = []
            missing_modules = []

            for module in required_modules:
                try:
                    if module == "yaml":
                        import yaml
                    else:
                        __import__(module)
                    available_modules.append(module)
                except ImportError:
                    missing_modules.append(module)

            if not missing_modules:
                check.pass_check(f"Python模块完整: {len(available_modules)}个")
            else:
                check.fail_check(
                    f"缺少Python模块: {', '.join(missing_modules)}",
                    "运行 'pip install -e .' 或 'poetry install' 安装依赖"
                )

        except Exception as e:
            check.fail_check(f"Python模块检查失败: {e}")

        return check

    def check_network_connectivity(self) -> SystemCheck:
        """检查网络连接"""
        check = self.add_check(SystemCheck(
            "网络连接",
            "验证网络连接和外部服务可达性"
        ))

        try:
            if not self.network_available:
                check.skip_check("网络连接不可用（离线模式）")
                return check

            # 测试关键服务
            services = {
                "DNS": ("8.8.8.8", 53),
                "HTTPS": ("www.google.com", 443),
                "GitHub": ("github.com", 443)
            }

            working_services = []
            failed_services = []

            for service, (host, port) in services.items():
                try:
                    socket.create_connection((host, port), timeout=5)
                    working_services.append(service)
                except (OSError, socket.timeout):
                    failed_services.append(service)

            if not failed_services:
                check.pass_check(f"网络服务可达: {', '.join(working_services)}")
            elif len(failed_services) < len(services):
                check.pass_check(
                    f"部分网络服务可达: {', '.join(working_services)} "
                    f"(失败: {', '.join(failed_services)})"
                )
            else:
                check.fail_check(
                    f"所有网络服务不可达: {', '.join(failed_services)}",
                    "检查网络连接和防火墙设置"
                )

        except Exception as e:
            check.fail_check(f"网络连接检查失败: {e}")

        return check

    def check_launcher_script(self) -> SystemCheck:
        """检查启动器脚本"""
        check = self.add_check(SystemCheck(
            "启动器脚本",
            "验证bin/pm-local启动器是否正常工作"
        ))

        try:
            launcher_path = Path("bin/pm-local")

            if not launcher_path.exists():
                check.fail_check(
                    "启动器脚本不存在",
                    "确保从项目根目录运行，并检查bin/pm-local文件"
                )
                return check

            # 检查可执行权限
            if not os.access(launcher_path, os.X_OK):
                check.fail_check(
                    "启动器脚本无执行权限",
                    f"运行: chmod +x {launcher_path}"
                )
                return check

            # 测试启动器
            try:
                result = subprocess.run(
                    [str(launcher_path), "--launcher-debug"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    check.pass_check("启动器脚本工作正常")
                else:
                    check.fail_check(
                        f"启动器脚本执行失败: {result.stderr}",
                        "检查Python环境和项目依赖"
                    )
            except subprocess.TimeoutExpired:
                check.fail_check(
                    "启动器脚本响应超时",
                    "检查系统性能和依赖完整性"
                )

        except Exception as e:
            check.fail_check(f"启动器脚本检查失败: {e}")

        return check

    def check_memory_usage(self) -> SystemCheck:
        """检查内存使用情况"""
        check = self.add_check(SystemCheck(
            "内存使用",
            "验证系统内存是否充足"
        ))

        try:
            # 尝试获取内存信息
            if self.platform_info["system"] in ["linux", "wsl"]:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    mem_total = None
                    mem_available = None

                    for line in meminfo.split("\n"):
                        if line.startswith("MemTotal:"):
                            mem_total = int(line.split()[1]) * 1024  # Convert KB to bytes
                        elif line.startswith("MemAvailable:"):
                            mem_available = int(line.split()[1]) * 1024

                    if mem_total and mem_available:
                        mem_total_mb = mem_total / (1024 * 1024)
                        mem_available_mb = mem_available / (1024 * 1024)

                        if mem_available_mb > 500:  # 500MB threshold
                            check.pass_check(
                                f"内存充足: {mem_available_mb:.0f}MB可用 / {mem_total_mb:.0f}MB总计"
                            )
                        else:
                            check.fail_check(
                                f"内存不足: {mem_available_mb:.0f}MB可用 / {mem_total_mb:.0f}MB总计",
                                "关闭不必要的程序以释放内存"
                            )
                    else:
                        check.skip_check("无法解析内存信息")
            elif self.platform_info["system"] == "macos":
                # macOS memory check
                try:
                    result = subprocess.run(
                        ["vm_stat"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        check.pass_check("内存状态检查完成（macOS）")
                    else:
                        check.skip_check("无法获取macOS内存信息")
                except subprocess.TimeoutExpired:
                    check.skip_check("内存检查超时")
            else:
                check.skip_check(f"不支持的平台: {self.platform_info['system']}")

        except Exception as e:
            check.skip_check(f"内存检查失败: {e}")

        return check
    
    def run_all_checks(self):
        """运行所有检查项"""
        console.print("🔍 [bold blue]PersonalManager 系统诊断[/bold blue]")
        console.print()

        # 显示系统信息
        self._display_platform_info()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:

            task = progress.add_task("运行系统检查...", total=None)

            # 运行所有检查
            self.check_python_version()
            self.check_python_modules()
            self.check_config_initialization()
            self.check_data_directories()
            self.check_tokens_directory()
            self.check_required_directories()
            self.check_disk_space()
            self.check_system_commands()
            self.check_environment_variables()
            self.check_permissions()
            self.check_launcher_script()
            self.check_network_connectivity()
            self.check_memory_usage()

        # 统计结果
        for check in self.checks:
            if check.status == "PASS":
                self.passed += 1
            elif check.status == "FAIL":
                self.failed += 1
            else:
                self.skipped += 1

    def _display_platform_info(self):
        """显示平台信息"""
        info_panel = Panel(
            f"[cyan]系统:[/cyan] {self.platform_info['system'].title()} {self.platform_info.get('release', '')}\n"
            f"[cyan]架构:[/cyan] {self.platform_info.get('machine', 'unknown')}\n"
            f"[cyan]Python:[/cyan] {sys.version.split()[0]}\n"
            f"[cyan]网络:[/cyan] {'可用' if self.network_available else '离线'}",
            title="🖥️  系统信息",
            border_style="blue"
        )
        console.print(info_panel)
        console.print()
    
    def display_results(self):
        """显示诊断结果"""
        # 创建结果表格
        table = Table(title="🩺 系统诊断结果")
        table.add_column("检查项", style="cyan", width=15)
        table.add_column("状态", width=8)
        table.add_column("详情", style="dim")
        
        for check in self.checks:
            if check.status == "PASS":
                status_style = "[green]✅ PASS[/green]"
            elif check.status == "FAIL":
                status_style = "[red]❌ FAIL[/red]"
            else:
                status_style = "[yellow]⚠️ SKIP[/yellow]"
            
            table.add_row(
                check.name,
                status_style,
                check.details
            )
        
        console.print(table)
        console.print()
        
        # 显示汇总
        total_checks = len(self.checks)
        if self.failed == 0:
            summary_style = "green"
            summary_icon = "✅"
            summary_text = "系统健康，所有检查通过"
        elif self.failed <= 2:
            summary_style = "yellow" 
            summary_icon = "⚠️"
            summary_text = "系统基本正常，有少量问题需要修复"
        else:
            summary_style = "red"
            summary_icon = "❌"
            summary_text = "系统存在多个问题，建议立即修复"
        
        console.print(Panel(
            f"[{summary_style}]{summary_icon} {summary_text}[/{summary_style}]\\n\\n"
            f"总计: {total_checks} 项检查\\n"
            f"[green]通过: {self.passed}[/green] | "
            f"[red]失败: {self.failed}[/red] | "
            f"[yellow]跳过: {self.skipped}[/yellow]",
            title="📊 诊断汇总",
            border_style=summary_style
        ))
        
        # 显示修复建议
        if self.failed > 0:
            console.print("\\n[bold yellow]🔧 修复建议:[/bold yellow]")
            for i, check in enumerate(self.checks, 1):
                if check.status == "FAIL" and check.fix_suggestion:
                    console.print(f"{i}. [red]{check.name}[/red]: {check.fix_suggestion}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "home": str(Path.home()),
            "config_path": str(self.config.config_file) if self.config else "N/A",
            "data_path": str(self.config.data_dir) if self.config else "N/A",
            "network_status": "available" if self.network_available else "offline",
            "shell": os.getenv("SHELL", "unknown"),
            "terminal": os.getenv("TERM", "unknown"),
            "lang": os.getenv("LANG", "unknown")
        }

@doctor_app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细系统信息"),
    fix: bool = typer.Option(False, "--fix", help="尝试自动修复可修复的问题"),
    quick: bool = typer.Option(False, "--quick", "-q", help="快速检查（跳过网络和性能测试）"),
    export: Optional[str] = typer.Option(None, "--export", help="导出诊断报告到文件")
) -> None:
    """运行PersonalManager系统诊断

    检查Python版本、配置状态、目录权限、磁盘空间、网络连接等关键系统环境。
    支持快速检查模式和详细报告导出。
    """
    
    doctor = PMDoctor()

    try:
        # 根据模式运行检查
        if quick:
            doctor._run_quick_checks()
        else:
            doctor.run_all_checks()

        doctor.display_results()

        if verbose:
            doctor._display_detailed_info()

        if export:
            doctor._export_report(export)

        if fix:
            doctor._attempt_auto_fix()

        # 设置退出码
        if doctor.failed > 0:
            console.print("\\n[red]退出码: 1 (存在失败的检查项)[/red]")
            raise typer.Exit(1)
        else:
            console.print("\\n[green]退出码: 0 (所有检查通过)[/green]")
            
    except KeyboardInterrupt:
        console.print("\\n[yellow]用户中断诊断[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\\n[red]诊断过程出现错误: {e}[/red]")
        if verbose:
            import traceback
            console.print("\\n[dim]详细错误信息:[/dim]")
            console.print(traceback.format_exc())
        raise typer.Exit(1)
        """运行快速检查（跳过网络和性能测试）"""
        console.print("⚡ [bold yellow]快速系统诊断[/bold yellow]")
        console.print()

        self._display_platform_info()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:

            task = progress.add_task("运行快速检查...", total=None)

            # 只运行核心检查
            self.check_python_version()
            self.check_python_modules()
            self.check_config_initialization()
            self.check_data_directories()
            self.check_system_commands()
            self.check_launcher_script()

        # 统计结果
        for check in self.checks:
            if check.status == "PASS":
                self.passed += 1
            elif check.status == "FAIL":
                self.failed += 1
            else:
                self.skipped += 1

    def _display_detailed_info(self):
        """显示详细系统信息"""
        console.print("\\n[bold blue]📋 详细系统信息:[/bold blue]")
        sys_info = self.get_system_info()

        # 创建信息树
        tree = Tree("🖥️ System Information")

        system_branch = tree.add("[cyan]系统信息[/cyan]")
        system_branch.add(f"Platform: {sys_info['platform']}")
        system_branch.add(f"Working Directory: {sys_info['working_directory']}")
        system_branch.add(f"User: {sys_info['user']}")
        system_branch.add(f"Home: {sys_info['home']}")

        python_branch = tree.add("[green]Python环境[/green]")
        python_branch.add(f"Version: {sys_info['python_version'].split()[0]}")
        python_branch.add(f"Executable: {sys_info['python_executable']}")

        pm_branch = tree.add("[blue]PersonalManager[/blue]")
        pm_branch.add(f"Config: {sys_info['config_path']}")
        pm_branch.add(f"Data: {sys_info['data_path']}")

        env_branch = tree.add("[purple]环境变量[/purple]")
        env_branch.add(f"Shell: {sys_info['shell']}")
        env_branch.add(f"Terminal: {sys_info['terminal']}")
        env_branch.add(f"Language: {sys_info['lang']}")
        env_branch.add(f"Network: {sys_info['network_status']}")

        console.print(tree)

    def _export_report(self, filename: str):
        """导出诊断报告"""
        try:
            from datetime import datetime

            report_content = f"# PersonalManager 诊断报告\\n\\n"
            report_content += f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"

            # 系统信息
            report_content += f"## 系统信息\\n\\n"
            sys_info = self.get_system_info()
            for key, value in sys_info.items():
                report_content += f"- **{key.replace('_', ' ').title()}:** {value}\\n"

            # 检查结果
            report_content += f"\\n## 诊断结果\\n\\n"
            report_content += f"- 总计: {len(self.checks)} 项检查\\n"
            report_content += f"- 通过: {self.passed}\\n"
            report_content += f"- 失败: {self.failed}\\n"
            report_content += f"- 跳过: {self.skipped}\\n\\n"

            # 详细检查结果
            report_content += f"### 详细检查结果\\n\\n"
            for check in self.checks:
                status_icon = "✅" if check.status == "PASS" else "❌" if check.status == "FAIL" else "⚠️"
                report_content += f"#### {status_icon} {check.name}\\n"
                report_content += f"**描述:** {check.description}\\n\\n"
                report_content += f"**状态:** {check.status}\\n\\n"
                if check.details:
                    report_content += f"**详情:** {check.details}\\n\\n"
                if check.fix_suggestion:
                    report_content += f"**修复建议:** {check.fix_suggestion}\\n\\n"
                report_content += "---\\n\\n"

            # 写入文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            console.print(f"\\n[green]✅ 诊断报告已导出到: {filename}[/green]")

        except Exception as e:
            console.print(f"\\n[red]❌ 导出报告失败: {e}[/red]")

    def _attempt_auto_fix(self):
        """尝试自动修复可修复的问题"""
        console.print("\\n[yellow]🔧 尝试自动修复...[/yellow]")

        fixed_count = 0

        for check in self.checks:
            if check.status == "FAIL":
                if check.name == "启动器脚本" and "无执行权限" in check.details:
                    try:
                        launcher_path = Path("bin/pm-local")
                        os.chmod(launcher_path, 0o755)
                        console.print(f"[green]✅ 修复了启动器脚本权限[/green]")
                        fixed_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ 修复启动器权限失败: {e}[/red]")

                elif check.name == "目录结构":
                    try:
                        if self.config and self.config.data_dir:
                            required_dirs = ["tasks", "habits", "projects", "logs", "backups", "tokens"]
                            for dir_name in required_dirs:
                                dir_path = self.config.data_dir / dir_name
                                if not dir_path.exists():
                                    dir_path.mkdir(parents=True, exist_ok=True)
                            console.print(f"[green]✅ 创建了缺失的目录结构[/green]")
                            fixed_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ 创建目录结构失败: {e}[/red]")

        if fixed_count > 0:
            console.print(f"\\n[green]🎉 成功修复了 {fixed_count} 个问题[/green]")
            console.print("[blue]建议重新运行诊断以验证修复结果[/blue]")
        else:
            console.print("\\n[yellow]⚠️ 没有找到可自动修复的问题[/yellow]")
            console.print("[blue]请根据上述修复建议手动处理问题[/blue]")

# 为了兼容性，添加别名
@doctor_app.command("check")
def check_alias(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细系统信息"),
    quick: bool = typer.Option(False, "--quick", "-q", help="快速检查")
) -> None:
    """pm doctor check 的别名"""
    main(verbose=verbose, quick=quick, fix=False, export=None)

@doctor_app.command("fix")
def fix_command() -> None:
    """尝试自动修复系统问题"""
    main(verbose=False, fix=True, quick=False, export=None)

@doctor_app.command("report")
def report_command(
    output: str = typer.Option("pm_diagnostic_report.md", "--output", "-o", help="报告输出文件名")
) -> None:
    """生成详细诊断报告"""
    main(verbose=True, fix=False, quick=False, export=output)

if __name__ == "__main__":
    doctor_app()