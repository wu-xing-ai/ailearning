#!/bin/bash

# 智能学习平台部署脚本
# 用法: ./deploy.sh [start|stop|restart|logs|status]

set -e

COMPOSE_FILE="docker-compose.yml"

start() {
    echo "🚀 启动服务..."
    docker compose -f $COMPOSE_FILE up -d --build
    echo "✅ 服务已启动"
    echo "📍 访问地址: http://localhost"
    echo "📍 API文档: http://localhost:8000/docs"
}

stop() {
    echo "🛑 停止服务..."
    docker compose -f $COMPOSE_FILE down
    echo "✅ 服务已停止"
}

restart() {
    stop
    start
}

logs() {
    docker compose -f $COMPOSE_FILE logs -f
}

status() {
    docker compose -f $COMPOSE_FILE ps
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|logs|status}"
        exit 1
        ;;
esac
