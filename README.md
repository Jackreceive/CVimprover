# AI Intern Match

AI 实习岗位匹配系统 MVP，包含注册登录、PDF 简历上传、岗位 JD 录入、AI 匹配分析、技能差距、简历修改建议、投递记录和状态看板。

## 技术栈

- FastAPI
- PostgreSQL
- SQLModel / SQLAlchemy
- Redis
- Celery
- 本地文件存储，可替换对象存储
- OpenAI 兼容 LLM API
- Docker / Docker Compose

## 启动

```bash
cp .env.example .env
docker compose up --build
```

打开：

```text
http://localhost:8000
```

API 文档：

```text
http://localhost:8000/docs
```

## LLM 配置

`.env` 中配置：

```bash
LLM_API_KEY=你的 API Key
LLM_BASE_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

如果没有配置 `LLM_API_KEY`，系统会使用本地关键词启发式分析，便于先完整跑通上传、分析和投递流程。

## 主要接口

- `POST /api/auth/register` 注册
- `POST /api/auth/login` 登录
- `POST /api/resumes` 上传 PDF 简历
- `POST /api/jobs` 保存岗位 JD
- `POST /api/matches` 创建匹配分析任务
- `GET /api/matches/{id}` 查询分析结果
- `POST /api/applications` 保存投递记录
- `PATCH /api/applications/{id}` 更新投递状态

## 本地开发

只启动依赖：

```bash
docker compose up postgres redis
```

后端：

```bash
cd backend
/opt/homebrew/bin/python3.12 -m venv ../.venv312
source ../.venv312/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/intern_match
export REDIS_URL=redis://localhost:6379/0
uvicorn app.main:app --reload
```

Worker：

```bash
cd backend
source ../.venv312/bin/activate
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/intern_match
export REDIS_URL=redis://localhost:6379/0
celery -A app.worker.celery_app worker --loglevel=info
```
