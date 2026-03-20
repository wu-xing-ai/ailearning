# Python 异步编程与前后端流式通信学习笔记

## 目录

1. [项目架构概览](#1-项目架构概览)
2. [SSE 流式通信原理](#2-sse-流式通信原理)
3. [Python async/await 核心概念](#3-python-asyncawait-核心概念)
4. [问题分析与修复](#4-问题分析与修复)
5. [完整代码流程](#5-完整代码流程)
6. [常见陷阱与最佳实践](#6-常见陷阱与最佳实践)

---

## 1. 项目架构概览

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   前端 (Vue)    │  ──HTTP──▶│  后端   │  ──HTTP──▶│   Ollama服务    │
│ localhost:5173  │  ◀──SSE──│  localhost:8000 │  ◀──流式──│ localhost:11434 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### 技术栈

| 层级 | 技术 | 作用 |
|------|------|------|
| 前端 | Vue 3 + Element Plus | 用户界面，发送请求，接收流式响应 |
| 后端 | FastAPI + Uvicorn | API 网关，处理业务逻辑 |
| AI服务 | Ollama | 本地大模型推理引擎 |

---

## 2. SSE 流式通信原理

### 什么是 SSE (Server-Sent Events)？

SSE 是一种**服务器向客户端推送数据**的技术，特点：
- 基于 HTTP 协议
- **单向通信**（服务器 → 客户端）
- **长连接**，持续推送
- 格式简单：`data: {内容}\n\n`

### SSE vs WebSocket

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| 通信方向 | 单向（服务器→客户端） | 双向 |
| 协议 | HTTP | WS/WSS |
| 断线重连 | 浏览器自动重连 | 需要手动实现 |
| 适用场景 | 实时通知、流式输出 | 聊天、游戏 |

### SSE 数据格式示例

```
data: {"content": "你"}\n\n
data: {"content": "好"}\n\n
data: {"done": true}\n\n
```

---

## 3. Python async/await 核心概念

### 3.1 同步 vs 异步

```python
# 同步代码 - 串行执行
def sync_example():
    result1 = slow_operation_1()  # 等待 2 秒
    result2 = slow_operation_2()  # 等待 2 秒
    # 总耗时: 4 秒

# 异步代码 - 并发执行
async def async_example():
    result1, result2 = await asyncio.gather(
        slow_operation_1(),  # 同时进行
        slow_operation_2()   # 同时进行
    )
    # 总耗时: 2 秒
```

### 3.2 async 函数的两种类型

这是理解本次 bug 的**关键知识点**：

```python
# 类型1: 普通 async 函数
async def fetch_data():
    await some_io_operation()
    return {"data": "result"}

# 调用后返回: coroutine 对象
# 需要 await 才能得到返回值

coroutine_obj = fetch_data()        # 返回 coroutine
result = await fetch_data()         # 返回 {"data": "result"}


# 类型2: async generator (异步生成器)
async def stream_data():
    for i in range(3):
        await asyncio.sleep(0.1)
        yield f"chunk_{i}"          # 注意: 使用 yield

# 调用后返回: async generator 对象
# 不需要 await，直接用 async for 遍历

async_gen = stream_data()           # 返回 async generator
async for chunk in async_gen:       # 直接遍历
    print(chunk)
```

### 3.3 对比表格

| 类型 | 定义方式 | 调用后返回 | 如何获取值 |
|------|----------|-----------|-----------|
| async function | `async def foo(): return x` | **coroutine** | `await foo()` |
| async generator | `async def foo(): yield x` | **async generator** | `async for x in foo()` |

### 3.4 嵌套调用的情况（本次 bug 的根源）

```python
# 外层是 async function
async def outer():
    # 内层返回 async generator
    return inner_generator()  # ❌ 问题在这里！

async def inner_generator():
    yield "data"

# 调用 outer() 返回 coroutine
# await outer() 后才能得到 async generator
```

---

## 4. 问题分析与修复

### 4.1 Bug 现象

前端显示：`[无响应内容]`

后端日志错误：
```
'async for' requires an object with __aiter__ method, got coroutine
```

### 4.2 问题定位

**文件**: `backend/main.py` 第 179 行

```python
# ❌ 修复前
if stream:
    generator = service.chat_completion(prompt, stream=True)
    return StreamHandler.create_stream(generator)
```

### 4.3 问题分析

```
调用链分析:

service.chat_completion(prompt, stream=True)
    │
    ├── chat_completion 是 async def 函数
    │   → 调用它返回 coroutine 对象
    │
    └── 传入 StreamHandler.create_stream()
        │
        └── async for chunk in generator:
            │
            └── generator 是 coroutine，不是 async generator
                → coroutine 没有 __aiter__ 方法
                → 报错！
```

### 4.4 修复方案

```python
# ✅ 修复后
if stream:
    generator = await service.chat_completion(prompt, stream=True)
    return StreamHandler.create_stream(generator)
```

**解释**: `await` 把 coroutine "解包" 成真正的返回值（async generator）

### 4.5 完整调用链（修复后）

```
1. 前端发送请求
   POST /api/ai/chat {"prompt": "你好", "stream": true}
   │
   ▼
2. 后端 main.py 接收
   generator = await service.chat_completion(...)  ← await 得到 async generator
   return StreamHandler.create_stream(generator)
   │
   ▼
3. OllamaService 生成流式数据
   async def _stream_completion():
       async for line in response.aiter_lines():
           yield chunk  ← 每次生成一小段
   │
   ▼
4. StreamHandler 转换为 SSE 格式
   async for chunk in generator:
       yield f"data: {json.dumps({'content': chunk})}\n\n"
   │
   ▼
5. 前端接收并显示
   reader.read() → 解析 SSE → 显示文本
```

---

## 5. 完整代码流程

### 5.1 前端发送请求 (Chat.vue)

```javascript
// 1. 构造请求
const requestData = {
    prompt: "你好",
    stream: true,
    modelConfig: { type: "ollama", name: "qwen2.5:latest" }
}

// 2. 发送 POST 请求
const response = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
})

// 3. 获取流式读取器
const reader = response.body.getReader()
const decoder = new TextDecoder()

// 4. 循环读取数据
while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.content) {
                fullResponse += data.content  // 拼接文本
            }
            if (data.done) {
                // 显示完整回复
                messages.value.push({
                    type: 'assistant',
                    content: fullResponse
                })
            }
        }
    }
}
```

### 5.2 后端处理请求 (main.py)

```python
@app.post("/api/ai/chat")
async def chat_with_ai(request: dict):
    prompt = request.get("prompt", "")
    stream = request.get("stream", False)
    model_config = request.get("modelConfig", {})

    # 获取对应的服务
    service = ollama_service  # 或其他厂商服务

    if stream:
        # 关键修复: 必须使用 await
        generator = await service.chat_completion(prompt, stream=True)
        return StreamHandler.create_stream(generator)
    else:
        response = await service.chat_completion(prompt, stream=False)
        return response
```

### 5.3 Ollama 服务 (ollama_service.py)

```python
class OllamaService:
    async def chat_completion(self, prompt: str, stream: bool = False):
        messages = self.context + [{"role": "user", "content": prompt}]

        if stream:
            # 返回 async generator
            return self._stream_completion(messages)
        else:
            return await self._generate_completion(messages)

    async def _stream_completion(self, messages) -> AsyncGenerator[str, None]:
        """异步生成器 - 逐步 yield 文本片段"""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            async with client.stream("POST", "/api/chat",
                json={"model": self.model_name, "messages": messages, "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]  # 逐字返回
```

### 5.4 流式响应处理器 (stream_handler.py)

```python
class StreamHandler:
    @staticmethod
    def create_stream(generator: AsyncGenerator[str, None]) -> StreamingResponse:
        async def event_stream():
            try:
                async for chunk in generator:
                    # 转换为 SSE 格式
                    data = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"

                # 发送完成信号
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )
```

---

## 6. 常见陷阱与最佳实践

### 陷阱 1: 忘记 await

```python
# ❌ 错误
result = async_function()  # 得到 coroutine，不是结果

# ✅ 正确
result = await async_function()  # 得到实际结果
```

### 陷阱 2: 混淆 coroutine 和 async generator

```python
# 判断类型
import inspect

async def func1():
    return "hello"

async def func2():
    yield "hello"

print(inspect.iscoroutine(func1()))      # True - 是 coroutine
print(inspect.isasyncgen(func2()))       # True - 是 async generator
```

### 陷阱 3: 在同步函数中调用异步函数

```python
# ❌ 错误 - 不能在同步函数中直接 await
def sync_func():
    result = await async_func()  # SyntaxError

# ✅ 正确 - 使用 asyncio.run()
def sync_func():
    result = asyncio.run(async_func())

# ✅ 或者把同步函数改成异步
async def async_func_wrapper():
    result = await async_func()
```

### 最佳实践

1. **命名规范**: async generator 函数名可以用 `_stream_` 前缀，如 `_stream_completion`

2. **类型注解**: 明确标注返回类型
   ```python
   async def get_data() -> dict:  # 返回 coroutine -> dict
       return {"data": "value"}

   async def stream_data() -> AsyncGenerator[str, None]:  # 返回 async generator
       yield "chunk"
   ```

3. **错误处理**: 在流式处理中捕获异常
   ```python
   async def event_stream():
       try:
           async for chunk in generator:
               yield f"data: {chunk}\n\n"
       except Exception as e:
           yield f"data: {json.dumps({'error': str(e)})}\n\n"
   ```

4. **资源清理**: 使用 `async with` 确保资源正确释放
   ```python
   async with httpx.AsyncClient() as client:
       # 自动处理连接的打开和关闭
       response = await client.get(url)
   ```

---

## 总结

### 本次修复的核心知识点

```
async def 外层函数():
    return async_generator()  # 返回 coroutine (需要 await)

await 外层函数()  # ← 得到 async generator
```

### 记忆口诀

> **async def + return = coroutine (需要 await)**
> **async def + yield = async generator (不需要 await)**

---

## 参考资料

- [Python asyncio 官方文档](https://docs.python.org/zh-cn/3/library/asyncio.html)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [MDN - Server-Sent Events](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events)
- [Ollama API 文档](https://github.com/ollama/ollama/blob/main/docs/api.md)
