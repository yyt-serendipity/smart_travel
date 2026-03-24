# Smart Journey 项目说明

## 1. 项目目标

这个项目是一个面向中国国内旅游场景的学生化综合平台，目标不是做复杂企业系统，而是把一套完整链路做清楚：

- 城市推荐
- 景点详情
- 景点级 AI 行程
- 旅游社区
- 独立后台管理

相比上一版，这次更强调两件事：

1. 代码结构要更好理解  
2. 景点不能只是城市的附属信息

## 2. 当前功能

### 用户端

- 首页展示推荐城市、热门景点、最新帖子
- 城市筛选与城市详情
- 景点详情页
- AI 行程规划，细化到景点和时段
- 登录注册
- 个人主页
- 发帖、浏览、点赞、评论

### 后台端

- 独立后台控制台 `/backoffice`
- Django Admin `/site-admin/`
- 城市管理
- 景点管理
- 社区帖子管理
- Excel 数据导入

## 3. Django 结构设计

### 3.1 为什么不再只用一个 `core`

原先业务代码几乎全部堆在 `apps/core` 中，虽然能跑，但不利于阅读和讲解。  
这次保留了 `core.models` 作为数据层，避免数据库迁移风险，同时把业务逻辑拆分到多个 app。

### 3.2 当前 app 划分

```text
apps/core
  - 只保留模型与兼容层

apps/users
  - 登录
  - 注册
  - 当前用户信息
  - 个人资料

apps/destinations
  - 首页概览
  - 城市列表 / 详情
  - 景点列表 / 详情
  - Excel 导入器

apps/planner
  - AI 行程生成
  - 我的行程

apps/community
  - 帖子列表 / 详情
  - 发帖
  - 点赞
  - 评论

apps/backoffice
  - 后台汇总
  - 城市管理 API
  - 景点管理 API
  - 帖子管理 API
  - Excel 导入 API
```

这种方式比较适合学生项目：

- 结构直观
- 讲解时可以按模块介绍
- 不需要处理复杂的跨 app 模型迁移

## 4. 数据模型

当前主要模型仍位于 `apps/core/models.py`：

- `TravelCity`
- `Attraction`
- `UserProfile`
- `TravelPlan`
- `TravelPost`
- `PostLike`
- `PostComment`

说明：

- 这样做是为了保住现有 MySQL 数据表
- 业务层已经按 app 拆开，但数据库不需要重建

## 5. 爬虫与数据导入

## 5.1 Excel 模板

系统导入的 Excel 列结构为：

```text
名字 | 链接 | 地址 | 介绍 | 开放时间 | 图片链接 | 评分 | 建议游玩时间 | 建议季节 | 门票 | 小贴士 | Page
```

这套结构同时适用于：

- 你已有的 `cities_data_excel`
- 新爬虫脚本输出的 Excel

## 5.2 新爬虫脚本

新脚本：

`backend/scripts/crawl_ctrip_city_sights.py`

抓取逻辑：

1. 进入城市景点列表页  
2. 抓取景点列表  
3. 进入每个景点详情页  
4. 提取景点名称、地址、介绍、开放时间、图片、评分、建议游玩时间、门票、小贴士  
5. 输出成与项目兼容的 Excel

### 当前真实抓取结果

已成功抓取并输出到：

`D:\My_py\test\crawled_city_excels`

已抓取城市：

- 北京
- 上海
- 成都
- 杭州
- 西安

## 5.3 数据导入策略

当前采用的策略是：

- 先写并验证新爬虫脚本
- 再用爬虫输出目录补充导入热门城市
- 由于爬虫当前只抓取了 5 个城市，完整库仍使用你提供的 `cities_data_excel` 作为主数据源

这种做法更稳妥：

- 有真实爬虫能力
- 不会因为站点反爬而导致整库没数据
- 可以持续增量抓取

## 6. AI 行程设计

这次 AI 规划的重点不是“写一段摘要”，而是把结果细化到景点和时段。

### 输入

- 目标城市
- 出发城市
- 天数
- 预算
- 同行方式
- 季节偏好
- 兴趣标签

### 输出

- 推荐城市
- 行程总摘要
- 预算拆分
- 必去景点
- 每日行程
  - 上午
  - 下午
  - 夜晚
- 每日动线建议
- 打包清单

### 实现方式

- 按兴趣标签给城市打分
- 再按兴趣和评分给景点排序
- 每天选 2 到 3 个景点
- 将景点拆进上午 / 下午 / 夜晚
- 输出更适合前端展示的结构化 JSON

## 7. 前端设计说明

## 7.1 用户端

用户端保留了统一品牌导航，但把数据类内容收回后台，不再在首页暴露统计板块。

这次的页面调整包括：

- 整体主体宽度拉宽
- 首页更强调城市和景点
- 新增景点详情页
- AI 结果页改成景点级展示
- 社区页改成更像 QQ 空间的信息流布局

## 7.2 后台端

后台端现在是独立布局：

- 左侧侧边栏
- 中间主工作区
- 不再复用用户端头部

这样更符合“后台是单独界面”的要求。

## 8. API 设计

### 用户与资料

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `GET /api/profile/me/`
- `PATCH /api/profile/me/`

### 城市与景点

- `GET /api/overview/`
- `GET /api/cities/`
- `GET /api/cities/{id}/`
- `GET /api/cities/recommend/`
- `GET /api/attractions/`
- `GET /api/attractions/{id}/`

### AI 行程

- `POST /api/planner/generate/`
- `GET /api/plans/`

### 社区

- `GET /api/posts/`
- `GET /api/posts/{id}/`
- `POST /api/posts/`
- `POST /api/posts/{id}/like/`
- `POST /api/posts/{id}/comment/`

### 后台

- `GET /api/backoffice/summary/`
- `POST /api/backoffice/import-excels/`
- `GET/POST/PUT/DELETE /api/backoffice/cities/`
- `GET/POST/PUT/DELETE /api/backoffice/attractions/`
- `GET/DELETE /api/backoffice/posts/`

## 9. 启动方式

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

## 10. 验证结果

当前已经完成：

- Django 语法编译检查通过
- `python manage.py check` 通过
- `npm run build` 通过
- 新爬虫脚本真实抓取成功
- 爬虫输出 Excel 成功写入新目录
- 后台接口抽检通过
- 景点详情接口抽检通过
- AI 行程接口抽检通过

## 11. 后续可以继续做的方向

- 给后台控制台拆成真正的多页面，而不只是 query tab
- 增加景点图片画廊
- 增加帖子回复输入框
- 增加收藏城市 / 收藏景点
- 增加地图与路线规划
- 继续扩大爬虫抓取城市覆盖面
