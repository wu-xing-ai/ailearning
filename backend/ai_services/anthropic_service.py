"""
Anthropic Claude服务实现
"""
import httpx
import json
from typing import AsyncGenerator, Dict, List
from .base import BaseAIService


class AnthropicService(BaseAIService):
    """Anthropic服务类，支持Claude系列模型"""

    def __init__(
        self,
        model_name: str = "claude-3-sonnet-20240229",
        api_key: str = None,
        api_url: str = "https://api.anthropic.com/v1",
        **kwargs
    ):
        super().__init__(model_name, api_key, api_url, **kwargs)

    async def chat_completion(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Dict | AsyncGenerator[str, None]:
        """
        与Claude模型交互

        Args:
            prompt: 用户输入的提示
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            响应字典或异步生成器
        """
        messages = self.context + [{"role": "user", "content": prompt}]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        # Claude不支持system角色在messages中，需要单独处理
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": stream
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
                response = await client.post(
                    f"{self.api_url}/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Claude的响应格式
                content = data["content"][0]["text"]

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

                async with client.stream(
                    "POST",
                    f"{self.api_url}/messages",
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data: "):
                                data_str = line[6:]
                                try:
                                    data = json.loads(data_str)

                                    # Claude的流式响应格式
                                    if data.get("type") == "content_block_delta":
                                        delta = data.get("delta", {})
                                        if "text" in delta:
                                            chunk = delta["text"]
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
                yield f"[错误] 无法连接到Anthropic服务"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        # Claude模型列表（静态）
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]
