# 多阶段构建 Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 安装依赖
RUN npm ci

# 构建应用
RUN npm run build

FROM nginx:alpine AS production
WORKDIR /usr/share/nginx/html

# 复制构建产物
COPY --from=builder /app/dist .

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]