"""Google OAuth 2.0 认证管理器 - Sprint 9-10 Google Services集成

专门处理Google服务的OAuth 2.0认证流程
"""

import json
import webbrowser
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
import structlog

from pm.core.config import PMConfig
from .oauth_manager import OAuthManager, OAuthTokenInfo
from .account_manager import AccountManager

logger = structlog.get_logger()

class GoogleAuthManager:
    """Google OAuth 2.0 认证管理器
    
    专门处理Google服务的OAuth 2.0认证流程，包括：
    - Google Calendar API
    - Google Tasks API  
    - Gmail API
    """
    
    # Google OAuth 2.0 端点
    GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    GOOGLE_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    
    # Google API 权限范围
    GOOGLE_SCOPES = {
        'calendar': 'https://www.googleapis.com/auth/calendar.readonly',  # 只读权限，更容易通过
        'calendar_full': 'https://www.googleapis.com/auth/calendar',      # 完整权限
        'tasks': 'https://www.googleapis.com/auth/tasks',
        'gmail': 'https://www.googleapis.com/auth/gmail.readonly'
    }
    
    # 最小权限集合（用于初始测试）
    MINIMAL_SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly'
    ]
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.oauth_manager = OAuthManager(config)
        self.account_manager = AccountManager(config)

        # 加载Google OAuth客户端配置
        self._credentials = self._load_google_credentials()
        self.client_id = self._get_google_client_id()
        self.client_secret = self._get_google_client_secret()
        self.redirect_uri = "http://localhost:8080/oauth/callback"

        logger.info("Google Auth Manager initialized",
                   has_credentials=bool(self._credentials),
                   client_id_set=bool(self.client_id))
    
    def start_google_auth(self, services: list = None, minimal: bool = False, account_alias: str = None) -> Tuple[str, str]:
        """启动Google OAuth认证流程
        
        Args:
            services: 需要授权的服务列表，默认为所有服务
            minimal: 是否使用最小权限集合（用于测试）
            account_alias: 账号别名，用于多账号管理

        Returns:
            Tuple[认证URL, state参数]
        """
        
        if minimal:
            # 使用最小权限集合进行测试
            scopes_str = ' '.join(self.MINIMAL_SCOPES)
            logger.info("Using minimal scopes for testing", scopes=self.MINIMAL_SCOPES)
        else:
            if services is None:
                services = ['calendar_full', 'tasks', 'gmail']
            
            # 构建权限范围
            scopes = []
            for service in services:
                if service in self.GOOGLE_SCOPES:
                    scopes.append(self.GOOGLE_SCOPES[service])
            
            scopes_str = ' '.join(scopes)
        
        # 生成认证URL
        auth_url, state = self.oauth_manager.generate_auth_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scopes=scopes_str,
            auth_endpoint=self.GOOGLE_AUTH_ENDPOINT,
            service_name="google"
        )
        
        if not minimal:
            logger.info("Generated Google auth URL", 
                       services=services, 
                       scopes_count=len(scopes))
        else:
            logger.info("Generated minimal Google auth URL", 
                       scopes_count=len(self.MINIMAL_SCOPES))
        
        return auth_url, state
    
    def handle_google_callback(self, callback_url: str) -> Tuple[bool, Optional[str]]:
        """处理Google OAuth回调
        
        Args:
            callback_url: 完整的回调URL
            
        Returns:
            Tuple[是否成功, 消息]
        """
        
        success, token_info, message = self.oauth_manager.handle_callback(
            callback_url=callback_url,
            token_endpoint=self.GOOGLE_TOKEN_ENDPOINT,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        if success and token_info:
            logger.info("Google authentication successful",
                       expires_at=token_info.expires_at)
            return True, "Google服务认证成功！"
        else:
            logger.error("Google authentication failed", message=message)
            return False, message
    
    def get_google_token(self, account_alias: str = None) -> Optional[OAuthTokenInfo]:
        """获取Google访问令牌

        Args:
            account_alias: 账号别名，如果为None则使用默认账号
        """
        if account_alias is None:
            account_alias = self.account_manager.get_default_account()

        return self.oauth_manager.get_token("google", account_alias)
    
    def is_google_authenticated(self, account_alias: str = None) -> bool:
        """检查是否已通过Google认证

        Args:
            account_alias: 账号别名，如果为None则使用默认账号
        """
        token = self.get_google_token(account_alias)
        return token is not None and not token.is_expired
    
    def revoke_google_auth(self) -> bool:
        """撤销Google认证"""
        
        # 首先尝试向Google服务器撤销token
        token = self.get_google_token()
        if token:
            try:
                # 实际实现中这里会发送HTTP请求到GOOGLE_REVOKE_ENDPOINT
                logger.info("Would revoke Google token", 
                           endpoint=self.GOOGLE_REVOKE_ENDPOINT)
            except Exception as e:
                logger.warning("Failed to revoke token with Google", error=str(e))
        
        # 删除本地存储的token
        return self.oauth_manager.revoke_token("google")
    
    def get_google_auth_status(self) -> Dict[str, Any]:
        """获取Google认证状态信息"""
        
        token = self.get_google_token()
        
        if not token:
            return {
                'authenticated': False,
                'message': '未认证'
            }
        
        if token.is_expired:
            return {
                'authenticated': False,
                'message': 'Token已过期',
                'expired_at': token.expires_at.isoformat() if token.expires_at else None
            }
        
        return {
            'authenticated': True,
            'message': '已认证',
            'expires_at': token.expires_at.isoformat() if token.expires_at else None,
            'scope': token.scope,
            'token_type': token.token_type
        }
    
    def _load_google_credentials(self) -> Optional[Dict[str, Any]]:
        """从credentials.json文件加载Google OAuth凭证
        
        Returns:
            凭证字典，如果加载失败则返回None
        """
        
        # 构建凭证文件路径
        credentials_path = Path.home() / ".personalmanager" / "credentials.json"
        
        try:
            if not credentials_path.exists():
                logger.warning("Google credentials file not found",
                             path=str(credentials_path))
                return None
            
            with open(credentials_path, 'r', encoding='utf-8') as f:
                credentials = json.load(f)
            
            # 验证凭证文件格式
            if self._validate_credentials_format(credentials):
                logger.info("Google credentials loaded successfully",
                           path=str(credentials_path))
                return credentials
            else:
                logger.error("Invalid credentials file format",
                           path=str(credentials_path))
                return None
                
        except json.JSONDecodeError as e:
            logger.error("Failed to parse credentials JSON file",
                        path=str(credentials_path),
                        error=str(e))
            return None
        except Exception as e:
            logger.error("Error loading Google credentials",
                        path=str(credentials_path),
                        error=str(e))
            return None
    
    def _validate_credentials_format(self, credentials: Dict[str, Any]) -> bool:
        """验证凭证文件格式是否正确
        
        Args:
            credentials: 凭证字典
            
        Returns:
            是否格式正确
        """
        
        # 检查是否包含必需的字段
        required_fields = ['client_id', 'client_secret']
        
        # 支持两种格式：
        # 1. 直接格式: {"client_id": "...", "client_secret": "..."}
        # 2. Google格式: {"web": {"client_id": "...", "client_secret": "..."}}
        
        # 检查直接格式
        if all(field in credentials for field in required_fields):
            return True
        
        # 检查Google标准格式
        if 'web' in credentials:
            web_config = credentials['web']
            if all(field in web_config for field in required_fields):
                return True
        
        # 检查installed app格式（桌面应用）
        if 'installed' in credentials:
            installed_config = credentials['installed']
            if all(field in installed_config for field in required_fields):
                return True
        
        return False
    
    def _get_google_client_id(self) -> str:
        """获取Google OAuth客户端ID
        
        Returns:
            客户端ID，如果加载失败则返回空字符串
        """
        
        if not self._credentials:
            logger.warning("No Google credentials available, using empty client_id")
            return ""
        
        # 尝试不同的格式
        if 'client_id' in self._credentials:
            return self._credentials['client_id']
        elif 'web' in self._credentials and 'client_id' in self._credentials['web']:
            return self._credentials['web']['client_id']
        elif 'installed' in self._credentials and 'client_id' in self._credentials['installed']:
            return self._credentials['installed']['client_id']
        
        logger.error("client_id not found in credentials")
        return ""
    
    def _get_google_client_secret(self) -> str:
        """获取Google OAuth客户端密钥
        
        Returns:
            客户端密钥，如果加载失败则返回空字符串
        """
        
        if not self._credentials:
            logger.warning("No Google credentials available, using empty client_secret")
            return ""
        
        # 尝试不同的格式
        if 'client_secret' in self._credentials:
            return self._credentials['client_secret']
        elif 'web' in self._credentials and 'client_secret' in self._credentials['web']:
            return self._credentials['web']['client_secret']
        elif 'installed' in self._credentials and 'client_secret' in self._credentials['installed']:
            return self._credentials['installed']['client_secret']
        
        logger.error("client_secret not found in credentials")
        return ""
    
    def is_credentials_configured(self) -> bool:
        """检查是否已正确配置Google凭证
        
        Returns:
            是否已配置凭证
        """
        return (self._credentials is not None and 
                bool(self.client_id) and 
                bool(self.client_secret) and
                self.client_id != "" and
                self.client_secret != "")
    
    def open_auth_url_in_browser(self, auth_url: str) -> None:
        """在浏览器中打开认证URL"""
        try:
            webbrowser.open(auth_url)
            logger.info("Opened auth URL in browser")
        except Exception as e:
            logger.warning("Failed to open browser", error=str(e))
            print(f"请手动打开以下链接进行认证: {auth_url}")

    def get_credentials_for_account(self, account_alias: str) -> Optional[Dict[str, Any]]:
        """获取指定账号的凭证信息"""
        credentials_path = self.account_manager.get_credentials_path(account_alias)
        if not credentials_path or not credentials_path.exists():
            return None

        try:
            with open(credentials_path, 'r', encoding='utf-8') as f:
                credentials = json.load(f)

            if self._validate_credentials_format(credentials):
                return credentials
            return None
        except Exception as e:
            logger.error("Error loading account credentials",
                        account=account_alias, error=str(e))
            return None

    def is_account_credentials_configured(self, account_alias: str) -> bool:
        """检查指定账号的凭证是否已配置"""
        credentials = self.get_credentials_for_account(account_alias)
        if not credentials:
            return False

        client_id = self._extract_client_id(credentials)
        client_secret = self._extract_client_secret(credentials)

        return bool(client_id) and bool(client_secret)

    def list_account_status(self) -> Dict[str, Dict[str, Any]]:
        """列出所有账号的认证状态"""
        accounts = self.account_manager.list_accounts()
        status = {}

        for alias, account_info in accounts.items():
            token = self.get_google_token(alias)
            status[alias] = {
                'display_name': account_info.get('display_name', alias),
                'email': account_info.get('email', ''),
                'authenticated': token is not None and not token.is_expired if token else False,
                'expired': token.is_expired if token else False,
                'expires_at': token.expires_at.isoformat() if token and token.expires_at else None,
                'credentials_configured': self.is_account_credentials_configured(alias)
            }

        return status

    def _extract_client_id(self, credentials: Dict[str, Any]) -> str:
        """从凭证中提取client_id"""
        if 'client_id' in credentials:
            return credentials['client_id']
        elif 'web' in credentials and 'client_id' in credentials['web']:
            return credentials['web']['client_id']
        elif 'installed' in credentials and 'client_id' in credentials['installed']:
            return credentials['installed']['client_id']
        return ""

    def _extract_client_secret(self, credentials: Dict[str, Any]) -> str:
        """从凭证中提取client_secret"""
        if 'client_secret' in credentials:
            return credentials['client_secret']
        elif 'web' in credentials and 'client_secret' in credentials['web']:
            return credentials['web']['client_secret']
        elif 'installed' in credentials and 'client_secret' in credentials['installed']:
            return credentials['installed']['client_secret']
        return ""