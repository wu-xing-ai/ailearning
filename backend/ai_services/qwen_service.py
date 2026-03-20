"""
阿里通义千问服务实现
"""
import httpx
import json
from typing import AsyncGenerator, Dict, List
from .base import BaseAIService


class QwenService(BaseAIService):
    """阿里通义千问服务类，支持Qwen系列模型"""

    def __init__(
        self,
        model_name: str = "qwen-turbo",
        api_key: str = None,
        api_url: str = "https://dashscope.aliyuncs.com/api/v1",
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
        与通义千问模型交互

        Args:
            prompt: 用户输入的提示
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            响应字典或异步生成器
        """
        messages = self.context + [{"role": "user", "content": prompt}]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 通义千问的请求格式
        payload = {
            "model": self.model_name,
            "input": {
                "messages": messages
            },
            "parameters": kwargs
        }

        if stream:
            headers["X-DashScope-SSE"] = "enable"

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
                    f"{self.api_url}/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # 通义千问的响应格式
                content = data["output"]["choices"][0]["message"]["content"]

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
                    f"{self.api_url}/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data:"):
                                data_str = line[5:].strip()
                                try:
                                    data = json.loads(data_str)
                                    output = data.get("output", {})
                                    choices = output.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("message", {})
                                        if "content" in delta:
                                            chunk = delta["content"].replace(full_content, "")
                                            if chunk:
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
                yield f"[错误] 无法连接到通义千问服务"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-longcontext",
            "qwen-long"
        ]
