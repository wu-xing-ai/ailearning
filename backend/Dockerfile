# syntax=docker/dockerfile:1
FROM python:3.10-slim AS base

WORKDIR /app

# 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 系统依赖（这一层会被 Docker 缓存）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# pip 镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# 先只复制依赖文件，利用 Docker 层缓存
COPY requirements.txt .

# 使用 BuildKit 缓存 mount，pip 下载的包持久化，不用每次重新下载
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 再复制代码（代码变了不影响上面的依赖缓存）
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
