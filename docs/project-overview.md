# Smart Travel 项目概览

## 1. 项目定位

`Smart Travel` 是一个围绕中国城市与景点内容构建的前后端分离旅游平台。当前版本聚焦四条主线：

- 城市与景点内容浏览
- AI 行程规划与问答助手
- 旅行社区内容沉淀
- 后台运营与内容维护

当前仓库以可运行、可部署、可演示为目标，不再沿用旧版“所有模型集中在 `apps/core/models.py`”的单体结构。

## 2. 当前功能清单

### 用户端

- 首页：默认推荐 + 登录后个性化推荐
- 城市列表、城市详情、天气、静态地图
- 景点列表、景点详情、相关推荐
- AI 行程规划：支持 `agent` / `qwen` 双模式
- AI 行程历史：登录用户自动保存，只展示当前用户自己的计划
- AI 页面恢复：从景点详情返回规划页时，可恢复上一次生成结果
- 问答助手：数据库 Agent 与千问直连双模式
- 社区帖子流、帖子详情、点赞、收藏、评论
- 登录、注册、个人主页、头像上传

### 管理端

- 后台工作台：`/backoffice`
- 总览页：5 个关键数字 + 运营总览板块
- 用户管理
- 城市管理
- 景点管理
- 帖子管理
- 操作日志查看
- Excel 导入 API 与上传导入接口

## 3. 当前代码结构

```text
backend/
├─ apps/
│  ├─ backoffice/     # 后台 API、运营日志、管理端聚合逻辑
│  ├─ community/      # 帖子、评论、点赞、收藏、帖子内容清洗
│  ├─ core/           # 权限、日志、上传、标签工具、迁移、管理命令
│  ├─ destinations/   # 城市/景点模型、首页推荐、天气地图、推荐模型、Excel 导入
│  ├─ planner/        # AI 行程、问答助手、历史行程读取与保存
│  └─ users/          # 登录注册、个人资料、上传入口
├─ smart_travel/      # Django settings / urls / wsgi / asgi
└─ manage.py

frontend/
├─ src/
│  ├─ components/     # 卡片、后台壳、帖子展示、问答组件、文件上传
│  ├─ router/         # 路由与管理员守卫
│  ├─ services/       # API 封装
│  ├─ stores/         # 认证状态与帖子互动状态
│  ├─ utils/          # 前端工具函数
│  └─ views/          # 页面级组件
└─ package.json

scripts/
└─ deploy_server.py   # 服务器覆盖部署脚本
```

## 4. 数据模型现状

模型代码已经拆分到各业务 app：

- `apps/users/models.py` -> `UserProfile`
- `apps/destinations/models.py` -> `TravelCity`、`Attraction`、`TravelCityGeoCache`、`UserAttractionRecommendationSnapshot`
- `apps/planner/models.py` -> `TravelPlan`
- `apps/community/models.py` -> `TravelPost`、`PostLike`、`PostFavorite`、`PostComment`
- `apps/backoffice/models.py` -> `OperationLog`

当前数据库物理表名已经统一改为无 `core_` 前缀：

- `user_profile`
- `travel_city`
- `attraction`
- `travel_city_geo_cache`
- `user_attraction_recommendation_snapshot`
- `travel_plan`
- `travel_post`
- `post_like`
- `post_favorite`
- `post_comment`
- `operation_log`

## 5. 当前实现中的几个重要变化

- `/site-admin/` 已不再作为独立后台入口维护。
- 社区发帖已改为轻量文本表单，后端再把纯文本转换为安全 HTML。
- AI 行程支持“自动保存 + 历史恢复 + 返回页恢复”。
- 后台总览只保留 5 个核心数字和运营总览板块。

## 6. 当前部署方式

本地开发：

- 前端通过 Vite 启动开发服务
- `/api` 由代理转发到 Django

生产环境：

- Nginx 托管 `frontend/dist`
- Nginx 反代 `/api/` 到 Gunicorn
- Gunicorn 承载 Django
- MySQL 保存业务数据

最近一次覆盖发布完成于 `2026-03-30`，公网入口为 `http://8.137.180.180/`。
