"""多账号管理器 - 支持多个Google账号"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog

from pm.core.config import PMConfig

logger = structlog.get_logger()


class AccountManager:
    """多账号管理器

    负责管理多个Google账号的配置、凭证和默认设置
    """

    def __init__(self, config: PMConfig):
        self.config = config
        self.accounts_config_file = config.data_dir / "accounts_config.json"
        self.credentials_dir = Path.home() / ".personalmanager"

        # 确保目录存在
        self.credentials_dir.mkdir(exist_ok=True)

        # 加载账号配置
        self._accounts_config = self._load_accounts_config()

        logger.info("AccountManager initialized",
                   accounts_count=len(self._accounts_config.get('accounts', {})))

    def _load_accounts_config(self) -> Dict[str, Any]:
        """加载账号配置文件"""
        if not self.accounts_config_file.exists():
            # 检查是否有现有的google_token.json，如果有则创建默认配置
            old_token_file = self.config.data_dir / "tokens" / "google_token.json"
            if old_token_file.exists():
                logger.info("Migrating existing Google token to multi-account structure")
                return self._create_default_config_from_existing()
            else:
                return self._create_default_config()

        try:
            with open(self.accounts_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error loading accounts config", error=str(e))
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认账号配置"""
        config = {
            "default_account": "default",
            "accounts": {
                "default": {
                    "display_name": "默认账号",
                    "email": "",
                    "services": ["calendar", "tasks", "gmail"],
                    "credentials_file": "credentials.json"
                }
            }
        }
        self._save_accounts_config(config)
        return config

    def _create_default_config_from_existing(self) -> Dict[str, Any]:
        """从现有token创建默认配置"""
        config = {
            "default_account": "default",
            "accounts": {
                "default": {
                    "display_name": "现有账号",
                    "email": "",
                    "services": ["calendar", "tasks", "gmail"],
                    "credentials_file": "credentials.json"
                }
            }
        }
        self._save_accounts_config(config)
        return config

    def _save_accounts_config(self, config: Dict[str, Any]) -> bool:
        """保存账号配置"""
        try:
            with open(self.accounts_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error("Error saving accounts config", error=str(e))
            return False

    def add_account(self, alias: str, display_name: str, email: str,
                   credentials_file: str = None, services: List[str] = None) -> bool:
        """添加新账号

        Args:
            alias: 账号别名
            display_name: 显示名称
            email: 邮箱地址
            credentials_file: 凭证文件名
            services: 支持的服务列表
        """
        if services is None:
            services = ["calendar", "tasks", "gmail"]

        if credentials_file is None:
            credentials_file = f"credentials_{alias}.json" if alias != "default" else "credentials.json"

        # 检查别名是否已存在
        if alias in self._accounts_config.get('accounts', {}):
            logger.warning("Account alias already exists", alias=alias)
            return False

        # 添加账号配置
        if 'accounts' not in self._accounts_config:
            self._accounts_config['accounts'] = {}

        self._accounts_config['accounts'][alias] = {
            "display_name": display_name,
            "email": email,
            "services": services,
            "credentials_file": credentials_file
        }

        # 如果是第一个账号，设置为默认
        if len(self._accounts_config['accounts']) == 1:
            self._accounts_config['default_account'] = alias

        success = self._save_accounts_config(self._accounts_config)
        if success:
            logger.info("Account added successfully", alias=alias, email=email)

        return success

    def remove_account(self, alias: str) -> bool:
        """移除账号"""
        if alias not in self._accounts_config.get('accounts', {}):
            logger.warning("Account not found", alias=alias)
            return False

        # 不允许删除默认账号
        if alias == self._accounts_config.get('default_account'):
            logger.warning("Cannot remove default account", alias=alias)
            return False

        # 删除账号配置
        del self._accounts_config['accounts'][alias]

        # 删除对应的token文件
        token_file = self.config.data_dir / "tokens" / f"google_{alias}_token.json"
        if token_file.exists():
            token_file.unlink()

        success = self._save_accounts_config(self._accounts_config)
        if success:
            logger.info("Account removed successfully", alias=alias)

        return success

    def set_default_account(self, alias: str) -> bool:
        """设置默认账号"""
        if alias not in self._accounts_config.get('accounts', {}):
            logger.warning("Account not found", alias=alias)
            return False

        self._accounts_config['default_account'] = alias
        success = self._save_accounts_config(self._accounts_config)

        if success:
            logger.info("Default account updated", alias=alias)

        return success

    def get_default_account(self) -> str:
        """获取默认账号别名"""
        return self._accounts_config.get('default_account', 'default')

    def get_account_info(self, alias: str) -> Optional[Dict[str, Any]]:
        """获取账号信息"""
        return self._accounts_config.get('accounts', {}).get(alias)

    def list_accounts(self) -> Dict[str, Dict[str, Any]]:
        """列出所有账号"""
        return self._accounts_config.get('accounts', {})

    def get_credentials_path(self, alias: str) -> Optional[Path]:
        """获取账号的凭证文件路径"""
        account_info = self.get_account_info(alias)
        if not account_info:
            return None

        credentials_file = account_info.get('credentials_file', 'credentials.json')
        return self.credentials_dir / credentials_file

    def migrate_existing_token(self) -> bool:
        """迁移现有的google_token.json到新的多账号结构"""
        old_token_file = self.config.data_dir / "tokens" / "google_token.json"
        new_token_file = self.config.data_dir / "tokens" / "google_default_token.json"

        if old_token_file.exists() and not new_token_file.exists():
            try:
                # 复制现有token到新文件名
                import shutil
                shutil.copy2(old_token_file, new_token_file)

                # 保留原文件，以防需要回滚
                logger.info("Migrated existing Google token",
                           from_file=str(old_token_file),
                           to_file=str(new_token_file))
                return True

            except Exception as e:
                logger.error("Error migrating token file", error=str(e))
                return False

        return True  # 如果没有需要迁移的文件，返回True

    def get_service_name_for_account(self, alias: str) -> str:
        """获取账号对应的服务名称（用于token文件命名）"""
        if alias == "default":
            return "google"  # 向后兼容
        return f"google_{alias}"