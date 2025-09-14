"""PersonalManager 异常处理模块"""

from typing import Optional


class PMError(Exception):
    """PersonalManager 基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PMExecutionError(PMError):
    """命令执行异常"""
    
    def __init__(self, message: str, exit_code: int = 1, command: Optional[str] = None):
        super().__init__(message, "EXECUTION_ERROR")
        self.exit_code = exit_code
        self.command = command


class PMSecurityError(PMError):
    """安全验证异常"""
    
    def __init__(self, message: str, dangerous_command: Optional[str] = None):
        super().__init__(message, "SECURITY_ERROR")
        self.dangerous_command = dangerous_command


class PMRoutingError(PMError):
    """路由解析异常"""
    
    def __init__(self, message: str, utterance: Optional[str] = None):
        super().__init__(message, "ROUTING_ERROR")
        self.utterance = utterance


class PMConfigurationError(PMError):
    """配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class PMIntegrationError(PMError):
    """第三方集成异常"""
    
    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(message, "INTEGRATION_ERROR")
        self.service = service