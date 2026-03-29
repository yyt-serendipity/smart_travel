# Smart Travel 项目概览

## 1. 项目定位

`Smart Travel` 是一个围绕中国城市与景点内容构建的前后端分离旅游平台，当前版本聚焦四条主线：

- 城市与景点内容浏览
- AI 行程规划与问答助手
- 旅行社区内容沉淀
- 后台管理与 Excel 数据导入

当前仓库以工程可运行性为主，不再维护旧版单体 `core/models.py` 结构，也不再维护 Docker 部署方案。

## 2. 当前功能清单

### 用户端

- 首页：省份入口卡片、热门城市、景点推荐、最新帖子
- 城市列表 / 城市详情
- 景点列表 / 景点详情
- AI 行程规划页，支持 `agent` 与 `qwen` 双模式
- 悬浮问答助手，支持数据库 Agent 与千问直连
- 社区帖子流、帖子详情、点赞、收藏、评论
- 登录、注册、个人主页、头像上传

### 管理端

- 独立后台工作台 `/backoffice`
- 用户管理
- 城市管理
- 景点管理
- 社区帖子管理
- 操作日志查看
- 浏览器上传 Excel 并导入数据库
- Django Admin `/site-admin/`

## 3. 当前代码结构

```text
backend/
├─ apps/
│  ├─ backoffice/     # 后台 API 与管理序列化
│  ├─ community/      # 帖子、评论、点赞、收藏、富文本清洗
│  ├─ core/           # 日志、权限、上传、标签工具、管理命令、迁移
│  ├─ destinations/   # 城市/景点模型、首页推荐、天气地图、推荐模型、Excel 导入
│  ├─ planner/        # AI 行程生成、规则回退、问答助手、已保存行程
│  └─ users/          # 登录注册、个人资料、上传入口
├─ smart_travel/      # Django settings / urls / wsgi / asgi
└─ manage.py

frontend/
├─ src/
│  ├─ components/     # 通用卡片、富文本、后台图表、问答组件
│  ├─ router/         # 路由与前端权限守卫
│  ├─ services/       # API 封装
│  ├─ stores/         # 本地认证与帖子互动状态
│  ├─ utils/          # 前端工具函数
│  └─ views/          # 页面级组件
└─ package.json

scripts/
└─ deploy_server.py   # 服务器自动部署脚本
```

## 4. 数据模型现状

模型代码已经拆分到各业务 app：

- `apps/users/models.py` -> `UserProfile`
- `apps/destinations/models.py` -> `TravelCity`、`Attraction`、`TravelCityGeoCache`、`UserAttractionRecommendationSnapshot`
- `apps/planner/models.py` -> `TravelPlan`
- `apps/community/models.py` -> `TravelPost`、`PostLike`、`PostFavorite`、`PostComment`
- `apps/backoffice/models.py` -> `OperationLog`

为了兼容历史数据表，模型仍保留：

```python
class Meta:
    app_label = "core"
```

因此数据库表名仍是 `core_*`，但模型代码已经不在 `apps/core/models.py`。

### 已删除的旧模型

- `Destination`
- `TripPlan`
- `TravelMapCache`
- `backend/apps/core/models.py` 旧入口文件

## 5. 首页推荐与个性化现状

首页接口是：`GET /api/overview/`

当前前后端配合方式如下：

1. 首屏先请求 `GET /api/overview/?mode=default`
2. 已登录用户再补请求 `GET /api/overview/?mode=personalized`
3. 前端用第二次返回结果覆盖默认推荐卡片

当前首页 payload 重点字段：

- `stats`
- `province_cards`
- `recommendation`
- `featured_cities`
- `spotlight_attractions`
- `latest_posts`
- `spotlight_model`
- `spotlight_profile`

## 6. AI 能力现状

### 6.1 问答助手

接口：`POST /api/assistant/chat/`

模式：

- `agent`：优先基于站内城市和景点库回答
- `qwen`：直接请求千问兼容接口

前端入口：`frontend/src/components/AssistantChatWidget.vue`

### 6.2 AI 行程规划

接口：`POST /api/planner/generate/`

模式：

- `agent`：把可用景点池提供给大模型，再把结果标准化为前端固定结构
- `qwen`：直接让模型输出 JSON 行程
- 任一模式失败时，都会回退到规则规划

返回重点字段：

- `planner_strategy`
- `planner_mode`
- `planner_provider`
- `planner_model`
- `fallback_reason`
- `used_fallback`
- `itinerary`
- `budget_breakdown`

## 7. 社区现状

社区接口由 `apps/community` 提供，当前已支持：

- 富文本发帖
- HTML 白名单清洗
- 点赞
- 收藏
- 评论
- 个人主页查看我的帖子 / 我的收藏

前端关键改动：

- 发帖改为弹窗式编辑器
- 使用 `RichTextEditor.vue` 与 `RichTextContent.vue`
- 帖子卡片与详情共享统一富文本渲染逻辑

## 8. 后台现状

后台前端入口：`/backoffice`

后台 API 前缀：`/api/backoffice/`

当前主要接口：

- `GET /api/backoffice/summary/`
- `GET/PUT/DELETE /api/backoffice/users/{id}/`
- `GET/POST/PUT/DELETE /api/backoffice/cities/`
- `GET/POST/PUT/DELETE /api/backoffice/attractions/`
- `GET/DELETE /api/backoffice/posts/`
- `GET /api/backoffice/logs/`
- `POST /api/backoffice/import-excels/upload/`

说明：浏览器上传导入是当前后台实际使用的 Excel 入口；`import-excels/` 目录导入接口保留给本地目录导入场景。

## 9. 数据导入与管理命令

当前可用命令：

- `python manage.py import_city_excels --directory "..."`
- `python manage.py seed_demo_data`
- `python manage.py normalize_tags`
- `python manage.py enrich_city_profiles`

说明：

- 旧文档中提到的 `backend/scripts/crawl_ctrip_city_sights.py` 当前仓库里已经不存在，不应再作为现行流程说明。
- 当前主数据入口是 Excel 导入，而不是仓库内爬虫脚本。

## 10. 本地启动

### 后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_city_excels --directory "C:/Users/YT-yuntian/Desktop/cities_data_excel"
python manage.py seed_demo_data
python manage.py runserver
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

## 11. 环境依赖

后端默认读取 `backend/.env`，主要环境变量分组如下：

- Django：`SECRET_KEY`、`DEBUG`、`ALLOWED_HOSTS`
- MySQL：`DB_NAME`、`DB_USER`、`DB_PASSWORD`、`DB_HOST`、`DB_PORT`
- OSS：`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET` 等
- LLM：`LLM_PROVIDER`、`DASHSCOPE_API_KEY`、`DASHSCOPE_MODEL`、`LLM_API_TIMEOUT`
- 高德：`AMAP_API_KEY`、`AMAP_BASE_URL`、`AMAP_REQUEST_TIMEOUT`

## 12. 推荐的校验命令

```powershell
cd backend
python manage.py check
python manage.py test -v 2 --noinput

cd ..\frontend
npm run build
```

## 13. 进一步阅读

- `docs/codebase-handbook.md`
- `docs/development-architecture-deployment-guide.md`
- `docs/project-development-handbook.md`
- `docs/assistant-chat-and-planner-modes.md`
- `docs/attraction-recommendation-model.md`
- `docs/planner-rule-fallback-design.md`
- `docs/ui-data-redesign-and-recommendation-cache.md`
