# syntax=docker/dockerfile:1

# ============ 构建阶段 ============
FROM python:3.10-slim AS builder

WORKDIR /app

# 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# pip 镜像加速（清华源）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装依赖（已移除重型依赖 sentence-transformers 和 chromadb）
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout=120 --retries=5 -r requirements.txt

# ============ 运行阶段 ============
FROM python:3.10-slim AS runtime

WORKDIR /app

# 只复制虚拟环境，不复制构建工具
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
