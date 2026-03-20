"""
Ollama服务模块 - 处理与本地Ollama模型的交互
"""
import httpx
import json
from typing import AsyncGenerator, Dict, List

# 导入基类（如果可用）
try:
    from ai_services.base import BaseAIService
    BASE_CLASS = BaseAIService
except ImportError:
    # 如果导入失败，使用普通类
    BASE_CLASS = object


class OllamaService(BASE_CLASS):
    """Ollama服务类，处理与本地Ollama模型的交互"""

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434", **kwargs):
        if BASE_CLASS != object:
            super().__init__(model_name, api_url=base_url, **kwargs)
        else:
            self.model_name = model_name
            self.base_url = base_url
            self.context: List[Dict] = []

        # 兼容两种模式
        if not hasattr(self, 'base_url'):
            self.base_url = base_url

    async def chat_completion(
        self, prompt: str, stream: bool = False, **kwargs
    ) -> Dict | AsyncGenerator:
        """
        与Ollama模型交互

        Args:
            prompt: 用户输入的提示
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整响应字典
            如果stream=True，返回异步生成器
        """
        messages = self.context + [{"role": "user", "content": prompt}]

        if stream:
            return self._stream_completion(messages)
        else:
            return await self._generate_completion(messages)

    async def _generate_completion(self, messages: List[Dict]) -> Dict:
        """
        生成完整响应（非流式）

        Args:
            messages: 消息历史列表

        Returns:
            包含响应内容的字典
        """
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            try:
                response = await client.post(
                    "/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
                content = data["message"]["content"]
                # 保存到上下文
                self.context.append({"role": "user", "content": messages[-1]["content"]})
                self.context.append({"role": "assistant", "content": content})
                return {"response": content, "model": self.model_name}

            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP错误: {e.response.status_code}"}
            except httpx.RequestError as e:
                return {"error": f"连接错误: {str(e)}，请确保Ollama正在运行"}
            except Exception as e:
                return {"error": f"发生错误: {str(e)}"}

    async def _stream_completion(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """
        生成流式响应

        Args:
            messages: 消息历史列表

        Yields:
            每次生成的文本片段
        """
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    "/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    response.raise_for_status()
                    full_content = ""

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    chunk = data["message"]["content"]
                                    full_content += chunk
                                    yield chunk
                                if data.get("done", False):
                                    # 保存到上下文
                                    self.context.append({"role": "user", "content": messages[-1]["content"]})
                                    self.context.append({"role": "assistant", "content": full_content})
                                    break
                            except json.JSONDecodeError:
                                continue

            except httpx.HTTPStatusError as e:
                yield f"[错误] HTTP错误: {e.response.status_code}"
            except httpx.RequestError as e:
                yield f"[错误] 无法连接到Ollama服务，请确保Ollama正在运行 (http://localhost:11434)"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    def reset_context(self):
        """重置对话上下文"""
        self.context = []

    def get_context(self) -> List[Dict]:
        """获取当前对话上下文"""
        return self.context.copy()

    async def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            try:
                response = await client.get("/api/tags")
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            except Exception:
                return []

    def update_model(self, model_name: str):
        """更新当前使用的模型"""
        self.model_name = model_name

    def update_base_url(self, base_url: str):
        """更新Ollama服务地址"""
        self.base_url = base_url
