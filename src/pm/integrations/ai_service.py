"""统一AI服务层 - Sprint 11-12核心功能

提供统一的大语言模型调用接口，支持多种AI服务提供商
"""

import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import structlog

from pm.core.config import PMConfig

logger = structlog.get_logger()


class AIProvider(str, Enum):
    """支持的AI服务提供商"""
    CLAUDE = "claude"
    GEMINI = "gemini"


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class AIServiceBase(ABC):
    """AI服务基础抽象类"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise AIServiceError(f"API key is required for {self.__class__.__name__}")
    
    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """生成文本响应"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class ClaudeService(AIServiceBase):
    """Claude AI服务实现"""
    
    API_BASE_URL = "https://api.anthropic.com/v1"
    MODEL_NAME = "claude-3-sonnet-20240229"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        logger.info("Claude AI service initialized")
    
    def generate_text(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """调用Claude API生成文本"""
        
        try:
            payload = {
                "model": self.MODEL_NAME,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            logger.info("Calling Claude API", model=self.MODEL_NAME, prompt_length=len(prompt))
            
            response = requests.post(
                f"{self.API_BASE_URL}/messages",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                logger.info("Claude API call successful", response_length=len(content))
                return content
            else:
                error_msg = f"Claude API error: {response.status_code} - {response.text}"
                logger.error("Claude API call failed", error=error_msg)
                raise AIServiceError(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Claude API network error: {str(e)}"
            logger.error("Claude API network error", error=str(e))
            raise AIServiceError(error_msg)
        except Exception as e:
            error_msg = f"Claude API unexpected error: {str(e)}"
            logger.error("Claude API unexpected error", error=str(e))
            raise AIServiceError(error_msg)
    
    def is_available(self) -> bool:
        """检查Claude服务是否可用"""
        try:
            # 发送一个简单的测试请求
            test_response = self.generate_text("Hello", max_tokens=10)
            return len(test_response) > 0
        except:
            return False


class GeminiService(AIServiceBase):
    """Gemini AI服务实现"""
    
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    MODEL_NAME = "gemini-pro"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        logger.info("Gemini AI service initialized")
    
    def generate_text(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """调用Gemini API生成文本"""
        
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            logger.info("Calling Gemini API", model=self.MODEL_NAME, prompt_length=len(prompt))
            
            response = requests.post(
                f"{self.API_BASE_URL}/models/{self.MODEL_NAME}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Gemini API call successful", response_length=len(content))
                return content
            else:
                error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                logger.error("Gemini API call failed", error=error_msg)
                raise AIServiceError(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Gemini API network error: {str(e)}"
            logger.error("Gemini API network error", error=str(e))
            raise AIServiceError(error_msg)
        except Exception as e:
            error_msg = f"Gemini API unexpected error: {str(e)}"
            logger.error("Gemini API unexpected error", error=str(e))
            raise AIServiceError(error_msg)
    
    def is_available(self) -> bool:
        """检查Gemini服务是否可用"""
        try:
            # 发送一个简单的测试请求
            test_response = self.generate_text("Hello", max_tokens=10)
            return len(test_response) > 0
        except:
            return False


class UnifiedAIService:
    """统一AI服务接口"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self._services: Dict[AIProvider, Optional[AIServiceBase]] = {}
        self._initialize_services()
        logger.info("Unified AI service initialized")
    
    def _initialize_services(self):
        """初始化所有可用的AI服务"""
        
        # 初始化Claude服务
        claude_key = self._get_api_key("claude")
        if claude_key:
            try:
                self._services[AIProvider.CLAUDE] = ClaudeService(claude_key)
                logger.info("Claude service initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize Claude service", error=str(e))
                self._services[AIProvider.CLAUDE] = None
        else:
            logger.info("Claude API key not found, skipping initialization")
            self._services[AIProvider.CLAUDE] = None
        
        # 初始化Gemini服务
        gemini_key = self._get_api_key("gemini")
        if gemini_key:
            try:
                self._services[AIProvider.GEMINI] = GeminiService(gemini_key)
                logger.info("Gemini service initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize Gemini service", error=str(e))
                self._services[AIProvider.GEMINI] = None
        else:
            logger.info("Gemini API key not found, skipping initialization")
            self._services[AIProvider.GEMINI] = None
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """安全地获取API密钥"""
        
        # 1. 首先检查环境变量
        env_var_map = {
            "claude": "PM_CLAUDE_API_KEY",
            "gemini": "PM_GEMINI_API_KEY"
        }
        
        env_key = os.getenv(env_var_map.get(provider, ""))
        if env_key:
            logger.debug(f"Found {provider} API key in environment")
            return env_key
        
        # 2. 然后检查配置对象
        config_attr_map = {
            "claude": "claude_api_key",
            "gemini": "gemini_api_key"
        }
        
        config_key = getattr(self.config, config_attr_map.get(provider, ""), None)
        if config_key:
            logger.debug(f"Found {provider} API key in config")
            return config_key
        
        return None
    
    def get_available_services(self) -> List[AIProvider]:
        """获取所有可用的AI服务"""
        available = []
        for provider, service in self._services.items():
            if service and service.is_available():
                available.append(provider)
        return available
    
    def generate_text(
        self, 
        prompt: str, 
        provider: Optional[AIProvider] = None,
        max_tokens: int = 4000,
        temperature: float = 0.1
    ) -> str:
        """生成文本响应
        
        Args:
            prompt: 输入提示词
            provider: 指定AI服务提供商，如果不指定则自动选择
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            生成的文本响应
            
        Raises:
            AIServiceError: 当没有可用服务或调用失败时
        """
        
        if not self.config.ai_tools_enabled:
            raise AIServiceError("AI tools are disabled in configuration")
        
        # 如果没有指定服务商，自动选择可用的
        if provider is None:
            available_services = self.get_available_services()
            if not available_services:
                raise AIServiceError("No AI services are available. Please check your API keys.")
            
            # 优先使用Claude，然后是Gemini
            if AIProvider.CLAUDE in available_services:
                provider = AIProvider.CLAUDE
            else:
                provider = available_services[0]
            
            logger.info(f"Auto-selected AI provider: {provider}")
        
        # 获取指定的服务
        service = self._services.get(provider)
        if not service:
            raise AIServiceError(f"AI service {provider} is not available")
        
        # 调用服务生成文本
        logger.info("Generating text", provider=provider, prompt_length=len(prompt))
        
        try:
            result = service.generate_text(prompt, max_tokens, temperature)
            logger.info("Text generation successful", provider=provider, result_length=len(result))
            return result
        except Exception as e:
            logger.error("Text generation failed", provider=provider, error=str(e))
            raise
    
    def is_any_service_available(self) -> bool:
        """检查是否有任何AI服务可用"""
        return len(self.get_available_services()) > 0
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务的状态信息"""
        status = {}
        
        for provider, service in self._services.items():
            if service:
                try:
                    available = service.is_available()
                    status[provider.value] = {
                        "initialized": True,
                        "available": available,
                        "error": None
                    }
                except Exception as e:
                    status[provider.value] = {
                        "initialized": True,
                        "available": False,
                        "error": str(e)
                    }
            else:
                status[provider.value] = {
                    "initialized": False,
                    "available": False,
                    "error": "API key not found or initialization failed"
                }
        
        return status