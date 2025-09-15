"""OAuth 2.0 认证管理器 - Sprint 9-10 核心基础设施

安全管理OAuth 2.0认证流程，支持token存储、刷新和撤销
"""

import json
import time
import secrets
import hashlib
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urlencode, parse_qs
import structlog

from pm.core.config import PMConfig

logger = structlog.get_logger()


class OAuthTokenInfo:
    """OAuth Token 信息封装"""
    
    def __init__(self, 
                 access_token: str,
                 refresh_token: Optional[str] = None,
                 expires_in: Optional[int] = None,
                 token_type: str = "Bearer",
                 scope: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.scope = scope
        
        # 计算过期时间
        if expires_in:
            self.expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 提前5分钟过期
        else:
            self.expires_at = None
    
    @property
    def is_expired(self) -> bool:
        """检查token是否已过期"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def authorization_header(self) -> str:
        """获取用于HTTP请求的Authorization头"""
        return f"{self.token_type} {self.access_token}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于存储"""
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'scope': self.scope,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuthTokenInfo':
        """从字典创建实例"""
        token = cls(
            access_token=data['access_token'],
            refresh_token=data.get('refresh_token'),
            token_type=data.get('token_type', 'Bearer'),
            scope=data.get('scope')
        )
        
        if data.get('expires_at'):
            token.expires_at = datetime.fromisoformat(data['expires_at'])
        
        return token


class OAuthManager:
    """OAuth 2.0 认证管理器
    
    负责管理OAuth 2.0认证流程的核心组件：
    - 生成认证URL
    - 处理回调和授权码交换
    - Token安全存储和自动刷新
    - 撤销访问权限
    """
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.tokens_dir = config.data_dir / "tokens"
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
        
        # OAuth 2.0 安全参数
        self._pending_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("OAuth Manager initialized", tokens_dir=self.tokens_dir)
    
    def generate_auth_url(self, 
                         client_id: str,
                         redirect_uri: str,
                         scopes: str,
                         auth_endpoint: str,
                         service_name: str) -> Tuple[str, str]:
        """生成OAuth认证URL和state参数
        
        Args:
            client_id: OAuth客户端ID
            redirect_uri: 重定向URI
            scopes: 请求的权限范围
            auth_endpoint: 认证端点URL
            service_name: 服务名称（用于标识）
            
        Returns:
            Tuple[认证URL, state参数]
        """
        
        # 生成安全的state参数防止CSRF攻击
        state = self._generate_secure_state()
        
        # 生成code_verifier和code_challenge (PKCE)
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        
        # 存储pending状态
        self._pending_states[state] = {
            'service_name': service_name,
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
            'created_at': datetime.now(),
            'client_id': client_id
        }
        
        # 构建认证URL
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scopes,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',  # 获取refresh_token
            'prompt': 'consent'        # 强制显示同意页面
        }
        
        auth_url = f"{auth_endpoint}?{urlencode(auth_params)}"
        
        logger.info("Generated OAuth auth URL",
                   service=service_name,
                   scopes=scopes,
                   state=state[:8])
        
        return auth_url, state
    
    def handle_callback(self, 
                       callback_url: str,
                       token_endpoint: str,
                       client_id: str,
                       client_secret: str) -> Tuple[bool, Optional[OAuthTokenInfo], str]:
        """处理OAuth回调并交换token
        
        Args:
            callback_url: 完整的回调URL
            token_endpoint: Token交换端点
            client_id: OAuth客户端ID
            client_secret: OAuth客户端密钥
            
        Returns:
            Tuple[是否成功, Token信息, 消息]
        """
        
        try:
            # 解析回调URL参数
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            
            # 检查是否有错误
            if 'error' in params:
                error = params['error'][0]
                error_desc = params.get('error_description', ['Unknown error'])[0]
                logger.error("OAuth callback error", error=error, description=error_desc)
                return False, None, f"认证失败: {error_desc}"
            
            # 验证必需参数
            if 'code' not in params or 'state' not in params:
                logger.error("Missing required callback parameters")
                return False, None, "回调参数不完整"
            
            auth_code = params['code'][0]
            state = params['state'][0]
            
            # 验证state参数
            if state not in self._pending_states:
                logger.error("Invalid or expired state parameter", state=state[:8])
                return False, None, "无效的状态参数，可能的CSRF攻击"
            
            state_info = self._pending_states[state]
            
            # 检查state是否过期（10分钟）
            if datetime.now() - state_info['created_at'] > timedelta(minutes=10):
                del self._pending_states[state]
                logger.error("Expired state parameter", state=state[:8])
                return False, None, "认证状态已过期，请重新运行 'pm auth login google'"
            
            # 交换授权码为访问令牌
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': state_info['redirect_uri'],
                'client_id': client_id,
                'client_secret': client_secret,
                'code_verifier': state_info['code_verifier']
            }
            
            # 发送HTTP POST请求到token_endpoint交换访问令牌
            logger.info("Exchanging auth code for tokens",
                       service=state_info['service_name'],
                       endpoint=token_endpoint)
            
            try:
                response = requests.post(
                    token_endpoint,
                    data=token_data,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'application/json'
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    token_response = response.json()
                    logger.info("Successfully received tokens from Google",
                              expires_in=token_response.get('expires_in'),
                              has_refresh_token=bool(token_response.get('refresh_token')))
                else:
                    error_msg = f"Token exchange failed: {response.status_code} - {response.text}"
                    logger.error("Token exchange failed", 
                               status_code=response.status_code,
                               response=response.text)
                    return False, None, error_msg
                    
            except requests.RequestException as e:
                error_msg = f"HTTP请求失败: {str(e)}"
                logger.error("HTTP request failed", error=str(e))
                return False, None, error_msg
            except Exception as e:
                error_msg = f"Token交换过程中发生错误: {str(e)}"
                logger.error("Token exchange error", error=str(e))
                return False, None, error_msg
            
            # 创建token信息
            token_info = OAuthTokenInfo(
                access_token=token_response['access_token'],
                refresh_token=token_response.get('refresh_token'),
                expires_in=token_response.get('expires_in'),
                token_type=token_response.get('token_type', 'Bearer'),
                scope=token_response.get('scope')
            )
            
            # 保存token
            service_name = state_info['service_name']
            self.save_token(service_name, token_info)
            
            # 清理pending状态
            del self._pending_states[state]
            
            logger.info("Successfully exchanged auth code for tokens",
                       service=service_name,
                       expires_at=token_info.expires_at)
            
            return True, token_info, f"{service_name}认证成功"
            
        except Exception as e:
            logger.error("Error handling OAuth callback", error=str(e))
            return False, None, f"处理认证回调时发生错误: {str(e)}"
    
    def get_token(self, service_name: str, account_alias: Optional[str] = None) -> Optional[OAuthTokenInfo]:
        """获取指定服务的有效token

        Args:
            service_name: 服务名称（如"google"）
            account_alias: 账号别名，如果为None则使用原service_name
        """

        # 如果指定了账号别名，构造带别名的服务名称
        if account_alias and account_alias != "default":
            token_service_name = f"{service_name}_{account_alias}"
        else:
            token_service_name = service_name

        token_file = self.tokens_dir / f"{token_service_name}_token.json"

        if not token_file.exists():
            return None

        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            token_info = OAuthTokenInfo.from_dict(token_data)

            # 检查是否过期
            if token_info.is_expired:
                logger.info("Token expired, attempting refresh",
                           service=token_service_name,
                           account=account_alias)
                # 尝试刷新token
                refreshed_token = self.refresh_token(token_service_name, token_info)
                if refreshed_token:
                    return refreshed_token
                return None

            return token_info

        except Exception as e:
            logger.error("Error loading token",
                        service=token_service_name,
                        account=account_alias,
                        error=str(e))
            return None
    
    def save_token(self, service_name: str, token_info: OAuthTokenInfo, account_alias: Optional[str] = None) -> bool:
        """安全保存token信息

        Args:
            service_name: 服务名称（如"google"）
            token_info: Token信息
            account_alias: 账号别名，如果为None则使用原service_name
        """

        # 如果指定了账号别名，构造带别名的服务名称
        if account_alias and account_alias != "default":
            token_service_name = f"{service_name}_{account_alias}"
        else:
            token_service_name = service_name

        token_file = self.tokens_dir / f"{token_service_name}_token.json"

        try:
            # 确保tokens目录权限安全
            self.tokens_dir.chmod(0o700)

            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_info.to_dict(), f, indent=2)

            # 设置文件权限为仅当前用户可读写
            token_file.chmod(0o600)

            logger.info("Token saved securely",
                       service=token_service_name,
                       account=account_alias,
                       file=token_file.name)
            return True

        except Exception as e:
            logger.error("Error saving token",
                        service=token_service_name,
                        account=account_alias,
                        error=str(e))
            return False
    
    def revoke_token(self, service_name: str) -> bool:
        """撤销并删除token"""
        
        token_file = self.tokens_dir / f"{service_name}_token.json"
        
        try:
            if token_file.exists():
                token_file.unlink()
                logger.info("Token revoked and deleted", service=service_name)
            
            return True
            
        except Exception as e:
            logger.error("Error revoking token", 
                        service=service_name, 
                        error=str(e))
            return False

    def refresh_token(self, service_name: str, token_info: OAuthTokenInfo) -> Optional[OAuthTokenInfo]:
        """刷新已过期的access token

        Args:
            service_name: 服务名称
            token_info: 当前的token信息

        Returns:
            刷新后的token信息，如果刷新失败则返回None
        """
        if not token_info.refresh_token:
            logger.warning("No refresh token available", service=service_name)
            return None

        try:
            import requests

            # Google的token刷新端点
            refresh_url = "https://oauth2.googleapis.com/token"

            # 准备刷新请求数据
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': token_info.refresh_token,
                'client_id': self._get_client_id_for_service(service_name),
                'client_secret': self._get_client_secret_for_service(service_name)
            }

            logger.info("Attempting to refresh token", service=service_name)

            # 发送刷新请求
            response = requests.post(refresh_url, data=refresh_data)

            if response.status_code == 200:
                token_response = response.json()

                # 创建新的token信息，保留原有的refresh_token
                new_token_info = OAuthTokenInfo(
                    access_token=token_response['access_token'],
                    refresh_token=token_info.refresh_token,  # 保持原有的refresh_token
                    expires_in=token_response.get('expires_in'),
                    token_type=token_response.get('token_type', 'Bearer'),
                    scope=token_response.get('scope', token_info.scope)
                )

                # 保存新的token
                if self.save_token(service_name, new_token_info):
                    logger.info("Token refreshed successfully",
                              service=service_name,
                              expires_at=new_token_info.expires_at.isoformat() if new_token_info.expires_at else None)
                    return new_token_info
                else:
                    logger.error("Failed to save refreshed token", service=service_name)
                    return None
            else:
                logger.error("Token refresh failed",
                           service=service_name,
                           status_code=response.status_code,
                           response=response.text)
                return None

        except Exception as e:
            logger.error("Error refreshing token", service=service_name, error=str(e))
            return None

    def _get_client_id_for_service(self, service_name: str) -> Optional[str]:
        """获取指定服务的client_id"""
        # 从Google credentials.json文件获取client_id
        try:
            from pathlib import Path
            import json

            credentials_path = Path.home() / ".personalmanager" / "credentials.json"
            if credentials_path.exists():
                with open(credentials_path, 'r', encoding='utf-8') as f:
                    credentials = json.load(f)
                    if 'installed' in credentials and 'client_id' in credentials['installed']:
                        return credentials['installed']['client_id']
        except Exception as e:
            logger.error("Error loading client_id from credentials", error=str(e))
        return None

    def _get_client_secret_for_service(self, service_name: str) -> Optional[str]:
        """获取指定服务的client_secret"""
        # 从Google credentials.json文件获取client_secret
        try:
            from pathlib import Path
            import json

            credentials_path = Path.home() / ".personalmanager" / "credentials.json"
            if credentials_path.exists():
                with open(credentials_path, 'r', encoding='utf-8') as f:
                    credentials = json.load(f)
                    if 'installed' in credentials and 'client_secret' in credentials['installed']:
                        return credentials['installed']['client_secret']
        except Exception as e:
            logger.error("Error loading client_secret from credentials", error=str(e))
        return None

    def list_authorized_services(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已授权的服务"""
        
        services = {}
        
        for token_file in self.tokens_dir.glob("*_token.json"):
            service_name = token_file.stem.replace('_token', '')
            
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                
                token_info = OAuthTokenInfo.from_dict(token_data)
                
                services[service_name] = {
                    'authorized': True,
                    'expires_at': token_info.expires_at.isoformat() if token_info.expires_at else None,
                    'is_expired': token_info.is_expired,
                    'scope': token_info.scope,
                    'token_type': token_info.token_type
                }
                
            except Exception as e:
                services[service_name] = {
                    'authorized': False,
                    'error': str(e)
                }
        
        return services
    
    def _generate_secure_state(self) -> str:
        """生成安全的state参数"""
        return secrets.token_urlsafe(32)
    
    def _generate_code_verifier(self) -> str:
        """生成PKCE code_verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    def _generate_code_challenge(self, code_verifier: str) -> str:
        """生成PKCE code_challenge"""
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    def cleanup_expired_states(self) -> None:
        """清理过期的pending状态"""
        
        current_time = datetime.now()
        expired_states = []
        
        for state, info in self._pending_states.items():
            if current_time - info['created_at'] > timedelta(minutes=10):
                expired_states.append(state)
        
        for state in expired_states:
            del self._pending_states[state]
        
        if expired_states:
            logger.info("Cleaned up expired states", count=len(expired_states))