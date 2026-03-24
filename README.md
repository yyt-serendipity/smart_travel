# Smart Journey 中国智能旅游平台

一个基于 `Django + Vue 3 + MySQL` 的学生化旅游项目，当前聚焦中国城市、景点详情、景点级 AI 行程、旅游社区和独立后台管理。

## 这次版本的重点

- 后端不再把业务逻辑都堆在一个 app 里
- 前台和后台使用两套独立布局
- 增加景点详情页
- AI 行程细化到景点和时段
- 旅游社区改成更像信息流的布局
- 新增携程爬虫脚本，可直接生成 Excel

## 当前后端结构

数据库模型仍放在 `apps/core/models.py` 里，保证现有数据表不需要高风险迁移；业务代码已经按模块拆开：

```text
backend/apps/
├─ core/           # 数据模型与兼容层
├─ users/          # 登录、注册、个人资料
├─ destinations/   # 城市、景点、首页、Excel 导入
├─ planner/        # AI 行程与已保存行程
├─ community/      # 帖子、点赞、评论
└─ backoffice/     # 后台控制台 API
```

这种拆法更适合课程项目和毕业设计：

- 目录更容易讲清楚
- 每个 app 的职责更单一
- 不需要为了拆 app 去重建数据库

## 前端页面

### 用户端

- `/` 首页
- `/cities` 城市推荐
- `/cities/:id` 城市详情
- `/attractions/:id` 景点详情
- `/planner` AI 行程规划
- `/community` 旅游社区
- `/community/:id` 帖子详情
- `/login` 登录
- `/register` 注册
- `/profile` 个人主页

### 后台端

- `/backoffice` 独立后台控制台
- `/site-admin/` Django Admin

## 数据策略

项目现在采用两层数据来源：

1. 优先使用新写的携程爬虫脚本，抓取城市 -> 景点列表 -> 景点详情，并生成 Excel  
2. 如果爬虫覆盖不够，再回退到你提供的 `cities_data_excel`

### 已生成的新爬虫数据

目录：

`D:\My_py\test\crawled_city_excels`

目前已真实抓取并生成工作簿：

- 北京
- 上海
- 成都
- 杭州
- 西安

### 已导入的数据库

当前库内数据来自：

- 你提供的 `cities_data_excel` 全量导入
- 新爬虫目录 `crawled_city_excels` 的 5 个热门城市补充导入

## 本地数据库

当前默认连接：

- `host`: `127.0.0.1`
- `port`: `3306`
- `user`: `root`
- `password`: `123456`
- `database`: `smart_travel`

## 快速启动

### 后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_city_excels --directory "C:/Users/YT-yuntian/Desktop/cities_data_excel"
python manage.py runserver
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

## 爬虫脚本

新脚本：

`backend/scripts/crawl_ctrip_city_sights.py`

示例：

```powershell
.\backend\.venv\Scripts\python.exe backend\scripts\crawl_ctrip_city_sights.py `
  --city-urls-file backend\scripts\ctrip_city_urls_sample.txt `
  --output-dir D:\My_py\test\crawled_city_excels `
  --max-pages 1 `
  --max-attractions 8
```

单城市示例：

```powershell
.\backend\.venv\Scripts\python.exe backend\scripts\crawl_ctrip_city_sights.py `
  --city-url https://you.ctrip.com/sight/chengdu104.html `
  --city-name 成都 `
  --output-dir D:\My_py\test\crawled_city_excels `
  --max-pages 1 `
  --max-attractions 5
```

## 演示账号

- 普通用户：`traveler / travel123456`
- 管理员：`admin / admin123456`

## 已完成验证

- `python manage.py check`
- `python -m compileall -q backend`
- `python manage.py seed_demo_data`
- `npm run build`
- 新爬虫脚本已真实抓取并成功输出 Excel
- `/api/overview/`
- `/api/cities/`
- `/api/attractions/{id}/`
- `/api/planner/generate/`
- `/api/auth/login/`
- `/api/backoffice/summary/`

## 详细文档

见 [docs/project-overview.md](docs/project-overview.md)。
