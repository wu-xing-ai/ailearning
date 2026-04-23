"""
ModelScope服务实现 - 官方免费模型
API文档: https://www.modelscope.cn/docs
"""
import os
import httpx
import json
from typing import AsyncGenerator, Dict, List
from .base import BaseAIService


class ModelScopeService(BaseAIService):
    """ModelScope服务类，提供官方免费模型供所有用户使用"""

    # 系统内置API Key，从环境变量读取
    DEFAULT_API_KEY = os.getenv("MODELSCOPE_API_KEY", "ms-4eeaabdf-6d4e-47bb-9c63-24492c7abd8f")

    # 支持的模型列表
    AVAILABLE_MODELS = [
        {"value": "MiniMax/MiniMax-M2.5", "label": "MiniMax-M2.5 (免费)"},
    ]

    def __init__(
        self,
        model_name: str = "MiniMax/MiniMax-M2.5",
        api_key: str = None,
        api_url: str = "https://api-inference.modelscope.cn",
        **kwargs
    ):
        # 使用系统内置API Key和URL（用户无需配置）
        effective_api_key = api_key or self.DEFAULT_API_KEY
        effective_api_url = api_url or "https://api-inference.modelscope.cn"
        super().__init__(model_name, effective_api_key, effective_api_url, **kwargs)

    async def chat_completion(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Dict | AsyncGenerator[str, None]:
        messages = self.context + [{"role": "user", "content": prompt}]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
        }

        if stream:
            return self._stream_completion(headers, payload, messages)
        else:
            return await self._generate_completion(headers, payload, messages)

    async def _generate_completion(self, headers, payload, messages) -> Dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                self.add_to_context("user", messages[-1]["content"])
                self.add_to_context("assistant", content)

                return {
                    "response": content,
                    "model": self.model_name,
                    "usage": data.get("usage", {})
                }

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("error", {}).get("message", str(e.response.text))
                except:
                    error_detail = e.response.text
                return {"error": f"HTTP错误 {e.response.status_code}: {error_detail}"}
            except httpx.RequestError as e:
                return {"error": f"连接错误: {str(e)}，请检查网络连接"}
            except Exception as e:
                return {"error": f"发生错误: {str(e)}"}

    async def _stream_completion(self, headers, payload, messages) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                full_content = ""
                async with client.stream(
                    "POST",
                    f"{self.api_url}/v1/chat/completions",
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
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        chunk = delta["content"]
                                        full_content += chunk
                                        yield chunk
                                except json.JSONDecodeError:
                                    continue

                self.add_to_context("user", messages[-1]["content"])
                self.add_to_context("assistant", full_content)

            except httpx.HTTPStatusError as e:
                yield f"[错误] HTTP错误: {e.response.status_code}"
            except httpx.RequestError as e:
                yield f"[错误] 无法连接到ModelScope服务"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    async def get_available_models(self) -> List[Dict]:
        return self.AVAILABLE_MODELS