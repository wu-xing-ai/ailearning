"""
AI服务基类 - 定义统一的AI服务接口
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional


class BaseAIService(ABC):
    """AI服务抽象基类"""

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        **kwargs
    ):
        """
        初始化AI服务

        Args:
            model_name: 模型名称
            api_key: API密钥（可选）
            api_url: API地址（可选）
            **kwargs: 其他配置参数
        """
        self.model_name = model_name
        self.api_key = api_key
        self.api_url = api_url
        self.config = kwargs
        self.context: List[Dict] = []

    @abstractmethod
    async def chat_completion(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Dict | AsyncGenerator[str, None]:
        """
        聊天完成接口

        Args:
            prompt: 用户输入的提示
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整响应字典
            如果stream=True，返回异步生成器
        """
        raise NotImplementedError

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表

        Returns:
            模型名称列表
        """
        raise NotImplementedError

    def reset_context(self):
        """重置对话上下文"""
        self.context = []

    def get_context(self) -> List[Dict]:
        """获取当前对话上下文"""
        return self.context.copy()

    def add_to_context(self, role: str, content: str):
        """
        添加消息到上下文

        Args:
            role: 角色（user/assistant）
            content: 消息内容
        """
        self.context.append({"role": role, "content": content})

    def update_model(self, model_name: str):
        """更新模型名称"""
        self.model_name = model_name

    @property
    def provider_name(self) -> str:
        """返回提供商名称"""
        return self.__class__.__name__.replace("Service", "").lower()
