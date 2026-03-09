# 法律咨询助手 - 部署指南

本文档提供了法律咨询助手平台的详细部署指南。

## 目录

- [环境要求](#环境要求)
- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [云服务部署](#云服务部署)
- [生产环境配置](#生产环境配置)
- [故障排查](#故障排查)

---

## 环境要求

### 最低配置

**后端:**
- Python 3.11+
- RAM: 512MB
- 存储: 1GB

**前端:**
- Node.js 18+
- RAM: 256MB
- 存储: 500MB

### 推荐配置

**小型部署 (100 用户/天):**
- CPU: 2 核
- RAM: 2GB
- 存储: 20GB

**中型部署 (1000 用户/天):**
- CPU: 4 核
- RAM: 4GB
- 存储: 50GB

---

## 本地部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd dialog_chat_room
```

### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加必要的配置

# 初始化数据库
python create_tables.py

# 启动服务
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
echo "VITE_API_URL=http://your-backend-url" > .env

# 开发构建
npm run build

# 生产构建（优化）
npm run build --prod

# 预览构建
npm run preview
```

### 4. 使用 Nginx 服务前端

**安装 Nginx:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

**Nginx 配置 (`/etc/nginx/sites-available/legal-consultation`):**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg) {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**启用配置:**

```bash
sudo ln -s /etc/nginx/sites-available/legal-consultation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Docker 部署

### 1. 创建 Dockerfile (后端)

**`backend/Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/chroma

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建 Dockerfile (前端)

**`frontend/Dockerfile`:**

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3. 创建 docker-compose.yml

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/legal
      - DATABASE_URL_SYNC=postgresql://postgres:password@postgres:5432/legal
    volumes:
      - backend-data:/app/data
    depends_on:
      - postgres
      - chromadb
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=legal
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  chromadb:
    image: chromadb/chromadb:latest
    volumes:
      - chroma-data:/chroma/chroma
    restart: unless-stopped

volumes:
  backend-data:
  postgres-data:
  chroma-data:
```

### 4. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 云服务部署

### 部署到阿里云 (推荐)

#### 1. 使用阿里云容器服务

```bash
# 构建镜像
docker build -t legal-consultation-backend ./backend
docker build -t legal-consultation-frontend ./frontend

# 推送到镜像仓库
docker tag legal-consultation-backend registry.cn-hangzhou.aliyuncs.com/your-namespace/legal-consultation-backend
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/legal-consultation-backend
```

#### 2. 配置负载均衡和 RDS

1. 创建 SLB 负载均衡
2. 配置 RDS PostgreSQL 数据库
3. 更新环境变量连接到 RDS

#### 3. 使用函数计算 FC

```yaml
# 函数计算配置示例
functions:
  legal-consultation:
    runtime: python3.11
    timeout: 60
    memorySize: 512MB
    diskSize: 512MB
```

### 部署到腾讯云

#### 1. 使用轻量应用服务器 Lighthouse

1. 创建应用
2. 上传代码或连接 Git 仓库
3. 配置环境变量
4. 启动应用

#### 2. 使用云服务器 CVM

1. 购买 ECS 实例
2. 配置安全组开放 80、443 端口
3. 按照本地部署步骤配置

---

## 生产环境配置

### 1. 使用 Gunicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0 \
  --port 8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### 2. 使用 Supervisor 管理进程

**`/etc/supervisor/conf.d/legal-consultation.conf`:**

```ini
[program:legal-consultation]
command=/path/to/venv/bin/gunicorn app.main:app --workers 4
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/legal-consultation.err.log
stdout_logfile=/var/log/legal-consultation.out.log
```

### 3. 配置 PostgreSQL

**创建数据库:**

```bash
sudo -u postgres psql

CREATE DATABASE legal;
CREATE USER legal_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE legal TO legal_user;
```

**迁移数据库:**

```bash
alembic upgrade head
```

### 4. 配置 HTTPS (Let's Encrypt)

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 5. 配置防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 环境变量配置清单

### 必需变量

```bash
# 后端
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
DATABASE_URL_SYNC=postgresql://user:password@host:5432/dbname
DASHSCOPE_API_KEY=your_api_key_here

# 前端
VITE_API_URL=https://your-api-domain.com
```

### 可选变量

```bash
# 后端
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
CHROMA_DB_PATH=./data/chroma
CHROMA_COLLECTION_NAME=legal_knowledge
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
CORS_ORIGINS=https://your-frontend-domain.com
SUMMARY_MESSAGE_THRESHOLD=10
SUMMARY_TOKEN_THRESHOLD=8000
```

---

## 健康检查

### 后端健康检查

```bash
curl http://localhost:8000/health
```

### 数据库连接检查

```python
# backend/scripts/check_db.py
import asyncio
from app.database import AsyncSessionLocal

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute("SELECT 1")
        print("Database connection OK")

if __name__ == "__main__":
    asyncio.run(check_db())
```

### 前端健康检查

```bash
curl http://localhost:5173/
```

---

## 备份策略

### 数据库备份

```bash
# 每日备份
0 2 * * * pg_dump -U postgres legal > backup_$(date +\%Y\%m\d%d).sql

# 保留 7 天
find /path/to/backups -name "backup_*.sql" -mtime +7 -delete
```

### ChromaDB 备份

```bash
# 备份 ChromaDB 数据
tar -czf chroma_backup_$(date +\%Y\%m\d%d).tar.gz ./data/chroma
```

---

## 监控

### 日志监控

- **后端日志**: `/var/log/legal-consultation/`
- **Nginx 日志**: `/var/log/nginx/`
- **应用日志**: 结构化日志输出

### 性能监控

推荐使用:
- Prometheus + Grafana
- 阿里云云监控
- 腾讯云监控

---

## 故障排查

### 后端无法启动

1. 检查 Python 版本: `python --version`
2. 检查端口占用: `lsof -i:8000`
3. 检查环境变量: `cat .env`
4. 查看日志: `tail -f logs/*.log`

### 前端无法连接后端

1. 检查后端是否运行: `curl http://localhost:8000/health`
2. 检查 CORS 配置
3. 检查 API URL 配置: `cat .env`

### 数据库连接失败

1. 检查数据库服务状态
2. 验证连接字符串
3. 检查防火墙规则

### SSE 流式响应中断

1. 检查 Nginx 代理配置
2. 增加超时设置
3. 检查网络稳定性

---

## 更新部署

### 零停机部署

```bash
# 拉下新代码
git pull

# 后端
cd backend
git pull
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart legal-consultation

# 前端
cd frontend
npm install
npm run build
sudo systemctl reload nginx
```

### 蓝绿部署

```bash
# 使用 Docker 时
docker-compose pull
docker-compose up -d
```

---

## 安全建议

1. **API Key 保护**: 使用环境变量，不要提交到代码仓库
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **CORS**: 限制 CORS 来源
4. **速率限制**: 配置 Nginx 或 API 速率限制
5. **输入验证**: 已有 Pydantic schema 验证
6. **SQL 注入**: 使用 SQLAlchemy ORM 防护
7. **日志脱敏**: 确保日志不包含敏感信息

---

## 联系支持

如有部署问题，请查看：
- GitHub Issues
- 项目 Wiki
- 技术支持邮箱
