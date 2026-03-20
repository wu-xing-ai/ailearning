"""
流式处理模块 - 处理SSE流式响应
"""
import json
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse


class StreamHandler:
    """流式响应处理器"""

    @staticmethod
    def create_stream(generator: AsyncGenerator[str, None]) -> StreamingResponse:
        """
        创建SSE流式响应

        Args:
            generator: 异步生成器，生成文本片段

        Returns:
            FastAPI StreamingResponse对象
        """
        async def event_stream():
            try:
                async for chunk in generator:
                    # SSE格式：data: {json}\n\n
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                # 发送完成信号
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    @staticmethod
    def create_json_stream(generator: AsyncGenerator[dict, None]) -> StreamingResponse:
        """
        创建JSON流式响应

        Args:
            generator: 异步生成器，生成字典

        Returns:
            FastAPI StreamingResponse对象
        """
        async def event_stream():
            try:
                async for data in generator:
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
