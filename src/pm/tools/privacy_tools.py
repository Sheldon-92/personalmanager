"""AI可调用的隐私保护和数据管理工具函数

提供数据隐私保护的AI可调用接口，包括：
- 查看隐私信息和数据存储状态
- 导出用户数据
- 创建数据备份
- 清理过期数据
- 完全清除所有数据
- 验证数据完整性
"""

import shutil
import json
import tarfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import structlog

from pm.core.config import PMConfig

logger = structlog.get_logger(__name__)


def get_privacy_information() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取数据隐私信息和存储状态
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 隐私信息)
    """
    try:
        logger.info("获取数据隐私信息")
        
        config = PMConfig()
        storage_info = config.get_data_storage_info()
        
        privacy_info = {
            'storage_location': str(storage_info['storage_location']),
            'storage_type': 'local_only',
            'cloud_sync_enabled': False,
            'data_encryption': 'filesystem_level',
            'estimated_storage_size': storage_info['estimated_storage_size'],
            'backup_enabled': storage_info['backup_enabled'],
            'data_retention_days': storage_info['data_retention_days'],
            'privacy_commitments': [
                '完全本地存储 - 所有数据仅存储在您的设备上',
                '零云端传输 - 不会上传任何个人数据到互联网',
                '开源透明 - 所有代码开源，可审核验证',
                '用户控制 - 您拥有数据的完全控制权',
                '随时导出 - 支持数据导出，避免锁定',
                '安全删除 - 提供完整的数据清除功能'
            ],
            'available_actions': [
                'export_data - 导出所有数据',
                'backup_data - 创建数据备份',
                'cleanup_old_data - 清理过期数据',
                'clear_all_data - 完全清除所有数据',
                'verify_data_integrity - 验证数据完整性'
            ],
            'data_categories': [
                '配置设置',
                '项目数据',
                '任务记录',
                '习惯跟踪',
                '日志文件',
                '备份文件'
            ],
            'information_timestamp': datetime.now().isoformat()
        }
        
        logger.info("隐私信息获取完成", storage_size=storage_info['estimated_storage_size'])
        return True, "隐私信息获取成功", privacy_info
        
    except Exception as e:
        logger.error("获取隐私信息失败", error=str(e))
        return False, f"获取信息失败: {str(e)}", None


def export_user_data(export_location: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    导出所有用户数据
    
    Args:
        export_location: 导出位置，为空则使用默认位置
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 导出信息)
    """
    try:
        logger.info("开始导出用户数据", export_location=export_location)
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，没有数据可导出", None
            
        # 确定导出位置
        if export_location:
            export_dir = Path(export_location)
        else:
            export_dir = Path.home() / "PersonalManager_Export"
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = export_dir / f"pm_data_{timestamp}"
        
        # 创建导出目录
        export_path.mkdir(parents=True, exist_ok=True)
        
        exported_items = []
        export_size = 0
        
        # 复制配置文件
        if config.config_file.exists():
            config_dest = export_path / "config.yaml"
            shutil.copy2(config.config_file, config_dest)
            exported_items.append("配置文件")
            export_size += config.config_file.stat().st_size
            
        # 复制数据目录
        if config.data_dir.exists():
            data_dest = export_path / "data"
            shutil.copytree(config.data_dir, data_dest, dirs_exist_ok=True)
            
            # 统计导出的数据类型
            data_categories = []
            for subdir in ['projects', 'tasks', 'habits', 'logs']:
                subdir_path = data_dest / subdir
                if subdir_path.exists():
                    data_categories.append(subdir)
                    # 计算大小
                    for file_path in subdir_path.rglob('*'):
                        if file_path.is_file():
                            export_size += file_path.stat().st_size
                            
            exported_items.extend(data_categories)
            
        # 创建导出清单
        manifest = {
            "export_timestamp": timestamp,
            "pm_version": "0.1.0", 
            "export_type": "full_backup",
            "export_size_bytes": export_size,
            "files_included": {
                "config": "config.yaml",
                "data": "data/",
                "projects": "data/projects/",
                "tasks": "data/tasks/",
                "habits": "data/habits/",
                "logs": "data/logs/"
            },
            "exported_categories": exported_items,
            "privacy_note": "此导出包含您的所有PersonalManager数据，请妥善保管",
            "restore_instructions": "将config.yaml复制回配置目录，data/目录复制回数据目录即可恢复"
        }
        
        manifest_path = export_path / "MANIFEST.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            
        export_result = {
            'export_successful': True,
            'export_path': str(export_path),
            'export_timestamp': timestamp,
            'exported_items': exported_items,
            'export_size_bytes': export_size,
            'export_size_mb': round(export_size / (1024 * 1024), 2),
            'manifest_file': str(manifest_path),
            'security_reminder': '请妥善保管导出的数据文件，避免泄露个人信息'
        }
        
        logger.info("用户数据导出完成", 
                   export_path=str(export_path),
                   size_mb=export_result['export_size_mb'])
        return True, f"数据导出成功，导出到 {export_path}", export_result
        
    except Exception as e:
        logger.error("用户数据导出失败", error=str(e))
        return False, f"导出失败: {str(e)}", None


def create_data_backup() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    创建数据备份
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 备份信息)
    """
    try:
        logger.info("开始创建数据备份")
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，没有数据需要备份", None
            
        backup_dir = config.data_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"pm_backup_{timestamp}.tar.gz"
        
        backup_size = 0
        backed_up_items = []
        
        with tarfile.open(backup_file, "w:gz") as tar:
            # 备份配置文件
            if config.config_file.exists():
                tar.add(config.config_file, arcname="config.yaml")
                backup_size += config.config_file.stat().st_size
                backed_up_items.append("配置文件")
                
            # 备份数据目录（除了备份目录本身）
            for item in config.data_dir.iterdir():
                if item.name != "backups" and item.is_dir():
                    tar.add(item, arcname=f"data/{item.name}")
                    backed_up_items.append(item.name)
                    
                    # 计算大小
                    for file_path in item.rglob('*'):
                        if file_path.is_file():
                            backup_size += file_path.stat().st_size
                            
        # 清理旧备份（保留最近10个）
        old_backups_cleaned = _cleanup_old_backups(backup_dir, keep=10)
        
        backup_result = {
            'backup_successful': True,
            'backup_file': str(backup_file),
            'backup_timestamp': timestamp,
            'backed_up_items': backed_up_items,
            'backup_size_bytes': backup_size,
            'backup_size_mb': round(backup_size / (1024 * 1024), 2),
            'old_backups_cleaned': old_backups_cleaned,
            'backup_retention_policy': '保留最近10个备份文件'
        }
        
        logger.info("数据备份创建完成", 
                   backup_file=str(backup_file),
                   size_mb=backup_result['backup_size_mb'])
        return True, f"备份创建成功: {backup_file}", backup_result
        
    except Exception as e:
        logger.error("数据备份创建失败", error=str(e))
        return False, f"备份失败: {str(e)}", None


def cleanup_old_data(retention_days: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    清理过期数据
    
    Args:
        retention_days: 数据保留天数，为空则使用配置中的默认值
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 清理信息)
    """
    try:
        logger.info("开始清理过期数据", retention_days=retention_days)
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，没有数据需要清理", None
            
        # 确定保留天数
        days = retention_days if retention_days is not None else config.data_retention_days
        cutoff_time = time.time() - (days * 24 * 3600)
        
        cleaned_files = []
        cleaned_size = 0
        
        # 清理日志文件
        logs_dir = config.data_dir / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned_files.append(f"日志文件: {log_file.name}")
                    cleaned_size += size
                    
        # 清理临时文件
        for temp_file in config.data_dir.rglob("*.tmp"):
            if temp_file.stat().st_mtime < cutoff_time:
                size = temp_file.stat().st_size
                temp_file.unlink()
                cleaned_files.append(f"临时文件: {temp_file.name}")
                cleaned_size += size
                
        # 清理缓存文件
        for cache_file in config.data_dir.rglob("*.cache"):
            if cache_file.stat().st_mtime < cutoff_time:
                size = cache_file.stat().st_size
                cache_file.unlink()
                cleaned_files.append(f"缓存文件: {cache_file.name}")
                cleaned_size += size
                
        # 清理旧备份
        backup_dir = config.data_dir / "backups"
        if backup_dir.exists():
            old_backups_cleaned = _cleanup_old_backups(backup_dir, keep=5)
            if old_backups_cleaned > 0:
                cleaned_files.append(f"旧备份文件: {old_backups_cleaned} 个")
                
        cleanup_result = {
            'cleanup_successful': True,
            'retention_days': days,
            'cutoff_timestamp': datetime.fromtimestamp(cutoff_time).isoformat(),
            'cleaned_files_count': len(cleaned_files),
            'cleaned_files': cleaned_files,
            'cleaned_size_bytes': cleaned_size,
            'cleaned_size_mb': round(cleaned_size / (1024 * 1024), 2),
            'cleanup_timestamp': datetime.now().isoformat()
        }
        
        logger.info("过期数据清理完成", 
                   files_cleaned=len(cleaned_files),
                   size_mb=cleanup_result['cleaned_size_mb'])
        return True, f"清理完成: {len(cleaned_files)} 个文件，{cleanup_result['cleaned_size_mb']} MB", cleanup_result
        
    except Exception as e:
        logger.error("过期数据清理失败", error=str(e))
        return False, f"清理失败: {str(e)}", None


def clear_all_data() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    完全清除所有数据 (危险操作)
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 清除信息)
    """
    try:
        logger.info("开始清除所有数据")
        
        config = PMConfig()
        
        cleared_items = []
        
        # 统计要删除的数据
        total_size = 0
        if config.config_file.exists():
            total_size += config.config_file.stat().st_size
            
        if config.data_dir.exists():
            for file_path in config.data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    
        # 删除配置文件
        if config.config_file.exists():
            config.config_file.unlink()
            cleared_items.append("配置文件")
            
        # 删除数据目录
        if config.data_dir.exists():
            # 记录删除的子目录
            for item in config.data_dir.iterdir():
                if item.is_dir():
                    cleared_items.append(f"数据目录: {item.name}")
                    
            shutil.rmtree(config.data_dir)
            
        # 尝试删除配置目录（如果为空）
        try:
            config.config_dir.rmdir()
            cleared_items.append("配置目录")
        except OSError:
            # 目录不为空，保留
            pass
            
        clear_result = {
            'clear_successful': True,
            'cleared_items': cleared_items,
            'total_size_cleared_bytes': total_size,
            'total_size_cleared_mb': round(total_size / (1024 * 1024), 2),
            'clear_timestamp': datetime.now().isoformat(),
            'warning': '所有数据已永久删除，下次运行需要重新设置',
            'recovery_note': '除非有备份文件，否则数据无法恢复'
        }
        
        logger.info("所有数据清除完成", 
                   items_cleared=len(cleared_items),
                   size_mb=clear_result['total_size_cleared_mb'])
        return True, f"所有数据已清除，共删除 {len(cleared_items)} 项，{clear_result['total_size_cleared_mb']} MB", clear_result
        
    except Exception as e:
        logger.error("数据清除失败", error=str(e))
        return False, f"清除失败: {str(e)}", None


def verify_data_integrity() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    验证数据完整性
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 验证信息)
    """
    try:
        logger.info("开始验证数据完整性")
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，没有数据需要验证", None
            
        issues = []
        checks_performed = []
        
        # 检查配置文件
        checks_performed.append("配置文件检查")
        if not config.config_file.exists():
            issues.append("配置文件缺失")
        else:
            try:
                config.load_from_file()
            except Exception as e:
                issues.append(f"配置文件损坏: {str(e)}")
                
        # 检查数据目录结构
        checks_performed.append("数据目录结构检查")
        required_dirs = ["projects", "tasks", "habits", "logs"]
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = config.data_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                issues.append(f"数据目录缺失: {dir_name}")
                
        # 检查项目文件夹
        checks_performed.append("项目文件夹检查")
        inaccessible_folders = []
        
        for project_folder in config.project_folders:
            folder_path = Path(project_folder)
            if not folder_path.exists():
                inaccessible_folders.append(project_folder)
                issues.append(f"项目文件夹不存在: {project_folder}")
            elif not folder_path.is_dir():
                inaccessible_folders.append(project_folder)
                issues.append(f"项目文件夹不是目录: {project_folder}")
                
        # 检查关键数据文件
        checks_performed.append("关键数据文件检查")
        data_file_issues = 0
        
        for data_dir in required_dirs:
            dir_path = config.data_dir / data_dir
            if dir_path.exists():
                for data_file in dir_path.rglob("*.json"):
                    try:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        issues.append(f"JSON文件损坏: {data_file.name} - {str(e)}")
                        data_file_issues += 1
                    except Exception as e:
                        issues.append(f"数据文件读取错误: {data_file.name} - {str(e)}")
                        data_file_issues += 1
                        
        # 生成验证报告
        integrity_status = "healthy" if not issues else "issues_found"
        
        verification_result = {
            'verification_successful': True,
            'integrity_status': integrity_status,
            'checks_performed': checks_performed,
            'total_issues': len(issues),
            'issues': issues,
            'statistics': {
                'missing_directories': len(missing_dirs),
                'inaccessible_project_folders': len(inaccessible_folders),
                'corrupted_data_files': data_file_issues
            },
            'repair_available': len(issues) > 0,
            'verification_timestamp': datetime.now().isoformat()
        }
        
        if issues:
            message = f"发现 {len(issues)} 个数据完整性问题"
            logger.warning("数据完整性验证发现问题", issues_count=len(issues))
        else:
            message = "数据完整性验证通过，所有数据正常"
            logger.info("数据完整性验证通过")
            
        return True, message, verification_result
        
    except Exception as e:
        logger.error("数据完整性验证失败", error=str(e))
        return False, f"验证失败: {str(e)}", None


def repair_data_issues() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    尝试自动修复数据问题
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 修复信息)
    """
    try:
        logger.info("开始自动修复数据问题")
        
        config = PMConfig()
        
        repaired_items = []
        repair_failures = []
        
        # 修复数据目录结构
        required_dirs = ["projects", "tasks", "habits", "logs", "backups"]
        for dir_name in required_dirs:
            dir_path = config.data_dir / dir_name
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    repaired_items.append(f"重建数据目录: {dir_name}")
                except Exception as e:
                    repair_failures.append(f"无法重建目录 {dir_name}: {str(e)}")
                    
        # 修复配置文件
        if not config.config_file.exists():
            try:
                # 确保配置目录存在
                config.config_dir.mkdir(parents=True, exist_ok=True)
                # 保存默认配置
                config.save_to_file()
                repaired_items.append("重建配置文件")
            except Exception as e:
                repair_failures.append(f"无法重建配置文件: {str(e)}")
                
        # 创建默认的README文件
        for dir_name in required_dirs[:4]:  # projects, tasks, habits, logs
            dir_path = config.data_dir / dir_name
            readme_path = dir_path / "README.md"
            if dir_path.exists() and not readme_path.exists():
                try:
                    readme_content = f"# {dir_name.capitalize()} Directory\n\n此目录用于存储 {dir_name} 相关数据。\n"
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(readme_content)
                    repaired_items.append(f"创建说明文件: {dir_name}/README.md")
                except Exception as e:
                    repair_failures.append(f"无法创建说明文件 {dir_name}/README.md: {str(e)}")
                    
        repair_result = {
            'repair_successful': True,
            'repaired_items_count': len(repaired_items),
            'repaired_items': repaired_items,
            'repair_failures_count': len(repair_failures),
            'repair_failures': repair_failures,
            'repair_timestamp': datetime.now().isoformat(),
            'recommendation': '修复完成后建议重新运行数据完整性验证'
        }
        
        if repaired_items:
            message = f"修复了 {len(repaired_items)} 个问题"
            if repair_failures:
                message += f"，{len(repair_failures)} 个问题修复失败"
        else:
            message = "没有可以自动修复的问题"
            
        logger.info("数据问题修复完成", 
                   repaired=len(repaired_items),
                   failed=len(repair_failures))
        return True, message, repair_result
        
    except Exception as e:
        logger.error("数据问题修复失败", error=str(e))
        return False, f"修复失败: {str(e)}", None


def get_storage_statistics() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取存储使用统计信息
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 存储统计)
    """
    try:
        logger.info("获取存储使用统计")
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，无法获取存储统计", None
            
        storage_stats = {
            'total_size_bytes': 0,
            'category_sizes': {},
            'file_counts': {},
            'largest_files': [],
            'oldest_files': [],
            'newest_files': []
        }
        
        all_files = []
        
        # 统计配置文件
        if config.config_file.exists():
            size = config.config_file.stat().st_size
            mtime = config.config_file.stat().st_mtime
            
            storage_stats['total_size_bytes'] += size
            storage_stats['category_sizes']['config'] = size
            storage_stats['file_counts']['config'] = 1
            
            all_files.append({
                'path': str(config.config_file),
                'category': 'config',
                'size': size,
                'mtime': mtime
            })
            
        # 统计数据目录
        if config.data_dir.exists():
            for category in ['projects', 'tasks', 'habits', 'logs', 'backups']:
                category_dir = config.data_dir / category
                if category_dir.exists():
                    category_size = 0
                    category_files = 0
                    
                    for file_path in category_dir.rglob('*'):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            mtime = file_path.stat().st_mtime
                            
                            category_size += size
                            category_files += 1
                            
                            all_files.append({
                                'path': str(file_path),
                                'category': category,
                                'size': size,
                                'mtime': mtime
                            })
                            
                    storage_stats['category_sizes'][category] = category_size
                    storage_stats['file_counts'][category] = category_files
                    storage_stats['total_size_bytes'] += category_size
                    
        # 找出最大的文件（前10个）
        all_files.sort(key=lambda x: x['size'], reverse=True)
        storage_stats['largest_files'] = all_files[:10]
        
        # 找出最老的文件（前10个）
        all_files.sort(key=lambda x: x['mtime'])
        storage_stats['oldest_files'] = all_files[:10]
        
        # 找出最新的文件（前10个）
        all_files.sort(key=lambda x: x['mtime'], reverse=True)
        storage_stats['newest_files'] = all_files[:10]
        
        # 转换为更友好的格式
        storage_stats['total_size_mb'] = round(storage_stats['total_size_bytes'] / (1024 * 1024), 2)
        storage_stats['total_files'] = len(all_files)
        
        for category in storage_stats['category_sizes']:
            size_mb = round(storage_stats['category_sizes'][category] / (1024 * 1024), 2)
            storage_stats['category_sizes'][category] = {
                'bytes': storage_stats['category_sizes'][category],
                'mb': size_mb
            }
            
        # 添加时间戳
        storage_stats['statistics_timestamp'] = datetime.now().isoformat()
        
        logger.info("存储统计获取完成", 
                   total_size_mb=storage_stats['total_size_mb'],
                   total_files=storage_stats['total_files'])
        return True, f"存储统计完成: {storage_stats['total_size_mb']} MB，{storage_stats['total_files']} 个文件", storage_stats
        
    except Exception as e:
        logger.error("获取存储统计失败", error=str(e))
        return False, f"统计失败: {str(e)}", None


def _cleanup_old_backups(backup_dir: Path, keep: int = 10) -> int:
    """清理旧备份文件，保留最近的几个"""
    
    try:
        backup_files = list(backup_dir.glob("pm_backup_*.tar.gz"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        cleaned_count = 0
        for old_backup in backup_files[keep:]:
            old_backup.unlink()
            cleaned_count += 1
            
        return cleaned_count
        
    except Exception as e:
        logger.error("清理旧备份文件失败", error=str(e))
        return 0