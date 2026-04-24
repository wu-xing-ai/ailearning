# syntax=docker/dockerfile:1
FROM node:20-alpine AS build
WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./

# 使用 BuildKit 缓存 npm 下载，不用每次重新拉包
RUN --mount=type=cache,target=/root/.npm \
    npm install --legacy-peer-deps

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
