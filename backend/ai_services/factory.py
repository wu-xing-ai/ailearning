"""
AI服务工厂 - 统一管理不同厂商的AI服务
"""
from typing import Dict, Optional
from .base import BaseAIService
from .openai_service import OpenAIService
from .anthropic_service import AnthropicService
from .zhipu_service import ZhipuService
from .qwen_service import QwenService
from .siliconflow_service import SiliconFlowService
from .custom_service import CustomService
from .modelscope_service import ModelScopeService


class AIServiceFactory:
    """AI服务工厂类，负责创建和管理不同厂商的AI服务实例"""

    # 服务类型映射
    _service_classes = {
        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "zhipu": ZhipuService,
        "qwen": QwenService,
        "siliconflow": SiliconFlowService,
        "custom": CustomService,
        "modelscope": ModelScopeService,
    }

    def __init__(self, default_provider: str = "ollama"):
        """
        初始化工厂

        Args:
            default_provider: 默认提供商
        """
        self._services: Dict[str, BaseAIService] = {}
        self._default_provider = default_provider
        self._api_keys: Dict[str, str] = {}

    def register_api_key(self, provider: str, api_key: str):
        """
        注册API密钥

        Args:
            provider: 提供商名称
            api_key: API密钥
        """
        self._api_keys[provider] = api_key

    def get_service(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> BaseAIService:
        """
        获取AI服务实例

        Args:
            provider: 提供商名称，如果为None则使用默认提供商
            model_name: 模型名称
            **kwargs: 其他配置参数

        Returns:
            AI服务实例

        Raises:
            ValueError: 如果提供商不存在
        """
        provider = provider or self._default_provider

        # 对于ollama，使用特殊的OllamaService
        if provider == "ollama":
            from ollama_service import OllamaService
            service_key = f"{provider}:{model_name or 'default'}"

            if service_key not in self._services:
                self._services[service_key] = OllamaService(
                    model_name=model_name or "llama3.2",
                    base_url=kwargs.get("base_url", "http://localhost:11434")
                )
            return self._services[service_key]

        # 其他厂商
        if provider not in self._service_classes:
            raise ValueError(f"不支持的提供商: {provider}")

        service_key = f"{provider}:{model_name or 'default'}"

        if service_key not in self._services:
            service_class = self._service_classes[provider]

            # 获取API密钥
            api_key = kwargs.get("api_key") or self._api_keys.get(provider)

            # 创建服务实例
            self._services[service_key] = service_class(
                model_name=model_name,
                api_key=api_key,
                api_url=kwargs.get("api_url"),
                **kwargs
            )

        return self._services[service_key]

    def create_service(
        self,
        provider: str,
        model_name: str,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        **kwargs
    ) -> BaseAIService:
        """
        创建新的AI服务实例（每次都创建新实例）

        Args:
            provider: 提供商名称
            model_name: 模型名称
            api_key: API密钥
            api_url: API地址
            **kwargs: 其他配置参数

        Returns:
            AI服务实例
        """
        # 对于ollama
        if provider == "ollama":
            from ollama_service import OllamaService
            return OllamaService(
                model_name=model_name,
                base_url=api_url or "http://localhost:11434"
            )

        # 其他厂商
        if provider not in self._service_classes:
            raise ValueError(f"不支持的提供商: {provider}")

        service_class = self._service_classes[provider]
        return service_class(
            model_name=model_name,
            api_key=api_key or self._api_keys.get(provider),
            api_url=api_url,
            **kwargs
        )

    def get_supported_providers(self) -> list:
        """获取支持的提供商列表"""
        return ["ollama"] + list(self._service_classes.keys())

    def clear_services(self):
        """清除所有缓存的服务实例"""
        self._services.clear()

    def remove_service(self, provider: str, model_name: Optional[str] = None):
        """
        移除指定的服务实例

        Args:
            provider: 提供商名称
            model_name: 模型名称，如果为None则移除该提供商的所有服务
        """
        keys_to_remove = [
            key for key in self._services
            if key.startswith(f"{provider}:")
        ]

        if model_name:
            specific_key = f"{provider}:{model_name}"
            if specific_key in keys_to_remove:
                keys_to_remove = [specific_key]
            else:
                keys_to_remove = []

        for key in keys_to_remove:
            del self._services[key]


# 全局工厂实例
factory = AIServiceFactory()
