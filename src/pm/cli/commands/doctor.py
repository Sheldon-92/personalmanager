"""系统环境与权限自检命令 - pm doctor

诊断PersonalManager运行环境，检查关键配置和依赖项
"""

import os
import sys
import shutil
import platform
from pathlib import Path
from typing import List, Tuple, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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
            required_commands = ["git"]  # 可扩展
            available_commands = []
            missing_commands = []
            
            for cmd in required_commands:
                if shutil.which(cmd):
                    available_commands.append(cmd)
                else:
                    missing_commands.append(cmd)
            
            if not missing_commands:
                check.pass_check(f"命令可用: {', '.join(available_commands)}")
            else:
                check.fail_check(
                    f"缺少命令: {', '.join(missing_commands)}",
                    "请安装缺少的命令工具"
                )
                
        except Exception as e:
            check.fail_check(f"命令检查失败: {e}")
        
        return check
    
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
    
    def run_all_checks(self):
        """运行所有检查项"""
        console.print("🔍 [bold blue]PersonalManager 系统诊断[/bold blue]")
        console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            
            task = progress.add_task("运行系统检查...", total=None)
            
            # 运行所有检查
            self.check_python_version()
            self.check_config_initialization() 
            self.check_data_directories()
            self.check_tokens_directory()
            self.check_required_directories()
            self.check_disk_space()
            self.check_system_commands()
            self.check_permissions()
        
        # 统计结果
        for check in self.checks:
            if check.status == "PASS":
                self.passed += 1
            elif check.status == "FAIL":
                self.failed += 1
            else:
                self.skipped += 1
    
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
            "data_path": str(self.config.data_dir) if self.config else "N/A"
        }

@doctor_app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细系统信息"),
    fix: bool = typer.Option(False, "--fix", help="尝试自动修复可修复的问题")
) -> None:
    """运行PersonalManager系统诊断
    
    检查Python版本、配置状态、目录权限、磁盘空间等关键系统环境
    """
    
    doctor = PMDoctor()
    
    try:
        doctor.run_all_checks()
        doctor.display_results()
        
        if verbose:
            console.print("\\n[bold blue]📋 系统信息:[/bold blue]")
            sys_info = doctor.get_system_info()
            info_table = Table(show_header=False, box=None)
            info_table.add_column("项目", style="cyan", width=20)
            info_table.add_column("值", style="dim")
            
            for key, value in sys_info.items():
                info_table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(info_table)
        
        if fix:
            console.print("\\n[yellow]⚠️ 自动修复功能将在后续版本中实现[/yellow]")
        
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
        raise typer.Exit(1)

# 为了兼容性，添加别名
@doctor_app.command("check")
def check_alias(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细系统信息")
) -> None:
    """pm doctor check 的别名"""
    main(verbose=verbose)

if __name__ == "__main__":
    doctor_app()