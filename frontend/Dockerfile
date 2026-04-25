# syntax=docker/dockerfile:1
# 用 Debian slim 替代 Alpine，避免 esbuild/vite 原生模块从源码编译
FROM node:20-slim AS build
WORKDIR /app

# npm 淘宝镜像加速
RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./

RUN npm install --legacy-peer-deps

COPY . .
ENV NODE_OPTIONS=--max-old-space-size=1024
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
