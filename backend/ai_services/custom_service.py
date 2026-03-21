"""
自定义API服务实现 - 支持自定义API端点
"""
import httpx
import json
from typing import AsyncGenerator, Dict, List
from .base import BaseAIService


class CustomService(BaseAIService):
    """自定义API服务类，支持OpenAI兼容的API端点"""

    def __init__(
        self,
        model_name: str = "custom-model",
        api_key: str = None,
        api_url: str = None,
        **kwargs
    ):
        super().__init__(model_name, api_key, api_url, **kwargs)

        # 自定义请求头
        self.custom_headers = kwargs.get("headers", {})

    async def chat_completion(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Dict | AsyncGenerator[str, None]:
        """
        与自定义模型交互

        Args:
            prompt: 用户输入的提示
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            响应字典或异步生成器
        """
        if not self.api_url:
            return {"error": "未配置API地址"}

        messages = self.context + [{"role": "user", "content": prompt}]

        headers = {
            "Content-Type": "application/json",
            **self.custom_headers
        }

        # 如果提供了API密钥，添加到请求头
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        if stream:
            return self._stream_completion(headers, payload, messages)
        else:
            return await self._generate_completion(headers, payload, messages)

    async def _generate_completion(
        self,
        headers: dict,
        payload: dict,
        messages: List[Dict]
    ) -> Dict:
        """生成完整响应"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # 构建API端点 - 支持多种URL格式
                base_url = self.api_url.rstrip('/')
                # 如果URL已经包含完整路径，直接使用；否则添加/v1/chat/completions
                if base_url.endswith('/chat/completions'):
                    endpoint = base_url
                elif '/v1' in base_url:
                    endpoint = f"{base_url}/chat/completions"
                else:
                    endpoint = f"{base_url}/v1/chat/completions"

                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # 尝试解析响应（兼容OpenAI格式）
                if "choices" not in data or not data["choices"]:
                    return {"error": f"API返回格式异常: {data}"}

                choice = data["choices"][0]
                if "message" not in choice:
                    return {"error": f"API返回格式异常(无message): {data}"}

                content = choice["message"].get("content", "")

                if not content:
                    return {"error": f"API返回空内容: {data}"}

                # 保存到上下文
                self.add_to_context("user", messages[-1]["content"])
                self.add_to_context("assistant", content)

                return {
                    "response": content,
                    "model": self.model_name,
                    "usage": data.get("usage", {})
                }

            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP错误: {e.response.status_code} - {e.response.text}"}
            except httpx.RequestError as e:
                return {"error": f"连接错误: {str(e)}"}
            except Exception as e:
                return {"error": f"发生错误: {str(e)}"}

    async def _stream_completion(
        self,
        headers: dict,
        payload: dict,
        messages: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                full_content = ""
                # 构建API端点 - 支持多种URL格式
                base_url = self.api_url.rstrip('/')
                if base_url.endswith('/chat/completions'):
                    endpoint = base_url
                elif '/v1' in base_url:
                    endpoint = f"{base_url}/chat/completions"
                else:
                    endpoint = f"{base_url}/v1/chat/completions"

                async with client.stream(
                    "POST",
                    endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    # 安全访问choices
                                    choices = data.get("choices", [])
                                    if choices and len(choices) > 0:
                                        delta = choices[0].get("delta", {})
                                        if "content" in delta:
                                            chunk = delta["content"]
                                            full_content += chunk
                                            yield chunk
                                except json.JSONDecodeError:
                                    continue

                # 保存到上下文
                self.add_to_context("user", messages[-1]["content"])
                self.add_to_context("assistant", full_content)

            except httpx.HTTPStatusError as e:
                yield f"[错误] HTTP错误: {e.response.status_code}"
            except httpx.RequestError as e:
                yield f"[错误] 无法连接到自定义API服务"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        # 对于自定义API，返回当前配置的模型
        return [self.model_name]
