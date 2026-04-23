"""
AI服务模块 - 提供统一的AI服务接口

支持的厂商：
- Ollama: 本地模型服务
- OpenAI: GPT系列模型
- Anthropic: Claude系列模型
- Zhipu: 智谱AI GLM系列模型
- Qwen: 阿里通义千问
- SiliconFlow: 硅基流动（多种开源模型）
- ModelScope: 官方免费模型
- Custom: 自定义API服务
"""

from .base import BaseAIService
from .factory import AIServiceFactory, factory
from .openai_service import OpenAIService
from .anthropic_service import AnthropicService
from .zhipu_service import ZhipuService
from .qwen_service import QwenService
from .siliconflow_service import SiliconFlowService
from .modelscope_service import ModelScopeService
from .custom_service import CustomService

__all__ = [
    "BaseAIService",
    "AIServiceFactory",
    "factory",
    "OpenAIService",
    "AnthropicService",
    "ZhipuService",
    "QwenService",
    "SiliconFlowService",
    "ModelScopeService",
    "CustomService"
]
