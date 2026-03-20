from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel

class AIRequest(BaseModel):
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 1.0
    stream: bool = False

class AIResponse(BaseModel):
    response: str
    model: str
    usage: Dict[str, int]
    finish_reason: str

class AIModelService(ABC):
    """AI模型服务的抽象基类"""

    @abstractmethod
    async def chat(self, request: AIRequest) -> AIResponse:
        """发送聊天请求到AI模型"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    def get_model_info(self, model_name: str) -> Dict:
        """获取模型信息"""
        pass

class ModelConfig:
    """模型配置类"""
    def __init__(self, name: str, provider: str, api_key: str,
                 endpoint: Optional[str] = None,
                 params: Optional[Dict] = None):
        self.name = name
        self.provider = provider
        self.api_key = api_key
        self.endpoint = endpoint
        self.params = params or {}

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "params": self.params
        }