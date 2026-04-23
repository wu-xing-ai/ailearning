#!/bin/bash

# 更新部署脚本
# 在服务器上执行: bash update.sh

cd /home/ubuntu/ailearning

# 解压最新代码
tar -xzvf ../update.tar.gz

# 重新构建并重启（数据库不受影响）
docker compose up -d --build

# 显示状态
docker compose ps
echo "更新完成！"
