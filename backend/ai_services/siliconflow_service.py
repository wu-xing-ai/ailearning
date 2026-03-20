"""
硅基流动服务实现 - 支持多种开源模型
API文档: https://docs.siliconflow.cn/
"""
import httpx
import json
from typing import AsyncGenerator, Dict, List
from .base import BaseAIService


class SiliconFlowService(BaseAIService):
    """硅基流动服务类，支持Qwen、DeepSeek、GLM等多种开源模型"""

    # 硅基流动免费模型列表
    FREE_MODELS = [
        "Qwen/Qwen2.5-7B-Instruct",
        "THUDM/glm-4-9b-chat",
        "THUDM/chatglm3-6b",
    ]

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        api_key: str = None,
        api_url: str = "https://api.siliconflow.cn/v1",
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
        与硅基流动模型交互

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

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7)
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
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]

                # 保存到上下文
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
                    f"{self.api_url}/chat/completions",
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

                # 保存到上下文
                self.add_to_context("user", messages[-1]["content"])
                self.add_to_context("assistant", full_content)

            except httpx.HTTPStatusError as e:
                yield f"[错误] HTTP错误: {e.response.status_code}"
            except httpx.RequestError as e:
                yield f"[错误] 无法连接到硅基流动服务"
            except Exception as e:
                yield f"[错误] 发生错误: {str(e)}"

    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        # 硅基流动常用模型列表
        return [
            # 免费模型
            "Qwen/Qwen2.5-7B-Instruct",
            "THUDM/glm-4-9b-chat",
            "THUDM/chatglm3-6b",
            # 付费模型
            "Qwen/Qwen2.5-72B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
            "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
        ]
