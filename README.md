# Smart Travel

`Smart Travel` 是一个围绕中国城市、景点、AI 行程和旅行社区构建的前后端分离项目。当前代码基于 `Django 5 + DRF`、`Vue 3 + Vite`、`MySQL`、阿里云 OSS、高德开放平台和千问兼容接口。

## 当前功能

- 首页两阶段推荐：首屏默认推荐，登录后再补个性化推荐。
- 城市与景点浏览：支持城市列表、城市详情、景点详情、天气和静态地图。
- AI 旅行规划：支持 `agent` 与 `qwen` 两种模式，失败时自动回退规则规划。
- AI 行程留存：登录用户生成行程时会自动保存，规划页支持历史记录和返回页恢复。
- 旅行社区：右侧使用轻量文本发帖表单，不再使用富文本编辑器。
- 管理后台：统一入口为 `/backoffice`，总览页只保留 5 个核心数字和运营总览。

## 技术栈

- 后端：`Django 5`、`Django REST Framework`
- 前端：`Vue 3`、`Vue Router`、`Axios`、`Vite`
- 数据库：`MySQL`
- 文件上传：`OSS`
- 地图与天气：`AMap API`
- AI：`DashScope / 通义千问兼容接口`

## 当前结构

```text
backend/
  apps/
    backoffice/
    community/
    core/
    destinations/
    planner/
    users/
frontend/
  src/
scripts/
  deploy_server.py
docs/
```

说明：

- 模型代码已经按业务 app 拆分，不再维护 `apps/core/models.py`。
- 为兼容历史迁移链，模型仍保留 `app_label = "core"`。
- 数据库物理表名已经移除 `core_` 前缀，例如 `travel_city`、`travel_plan`、`travel_post`。
- `/site-admin/` 已不再作为独立后台入口维护。

## 快速启动

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

## 常用校验

```powershell
cd backend
python manage.py check
python manage.py test -v 2 --noinput

cd ..\frontend
npm run build
```

## 当前生产部署

当前生产部署默认使用 `scripts/deploy_server.py` 覆盖远端目录并导入本地 MySQL dump。

最近一次覆盖发布完成于 `2026-03-30`：

- 服务器：`8.137.180.180`
- 部署目录：`/srv/smart_travel`
- 服务：`smart_travel`、`nginx`、`mysql`

## 文档索引

- `docs/README.md`
- `docs/project-overview.md`
- `docs/Smart Travel 代码总览手册.md`
- `docs/Smart Travel 架构与部署说明.md`
- `docs/Smart Travel 数据库设计.md`
- `docs/Smart Travel 生产发布记录与 Runbook.md`
- `docs/Smart Travel 项目开发手册.md`

## 说明

- 旧版文档中提到的仓库内爬虫脚本 `backend/scripts/crawl_ctrip_city_sights.py` 已不在当前仓库中。
- 现行主数据入口是 Excel 导入与后台上传导入。
