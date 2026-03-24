# Smart Travel 项目全量讲解手册

更新时间：2026-03-23

这份文档的目标不是简单重复 README，而是把这个项目按“能讲给老师/面试官/下一位开发者听”的方式完整拆开：

1. 这个项目现在到底是什么。
2. 后端、数据库、API、前端分别怎么组织。
3. 数据是怎么来的，页面是怎么跑起来的。
4. 当前代码里哪些地方已经够用，哪些地方适合下一阶段继续升级。

本文内容基于以下实际核查结果：

- 已逐个阅读 `backend/` 与 `frontend/src/` 的主要源码文件。
- 已连接项目默认 MySQL 数据库并核对当前真实表与数据量。
- 已执行 `python manage.py check`，结果通过。
- 已执行 `npm run build`，结果通过。

---

## 1. 项目一句话概括

`smart_travel` 是一个围绕“中国城市 + 景点 + AI 行程 + 社区 + 后台管理”构建的学生级完整旅游平台。

技术栈：

- 后端：Django 5.1 + Django REST Framework + Token Auth
- 前端：Vue 3 + Vue Router + Axios + Vite
- 数据库：MySQL 为默认主库，SQLite 作为备用回退
- 数据来源：本地 Excel + 携程页面爬虫输出的 Excel
- 媒体文件：当前保存在本地 `backend/media/`

这个项目的核心亮点不是“某一个复杂算法”，而是把一条完整业务链路做出来了：

- 城市与景点数据采集
- 数据导入与清洗
- 后端接口分层
- Vue 前端页面
- AI 行程规划
- 社区互动
- 后台管理

---

## 2. 当前实际运行状态

### 2.1 当前默认数据库

`backend/smart_travel/settings.py` 里默认走 MySQL：

- host: `127.0.0.1`
- port: `3306`
- database: `smart_travel`
- user: `root`
- password: `123456`

同时保留了 SQLite 分支：

- 当环境变量 `DB_ENGINE=sqlite` 时，数据库切到 `backend/db.sqlite3`

这说明：

1. 项目当前真实运行数据主要在 MySQL。
2. 仓库里的 `backend/db.sqlite3` 更像一个备用开发入口，不是当前主数据源。

### 2.2 截至 2026-03-23 的本地 MySQL 数据量

我直接用 Django ORM 核对了当前数据库：

| 数据对象 | 数量 |
| --- | ---: |
| 城市 `TravelCity` | 352 |
| 景点 `Attraction` | 30831 |
| 帖子 `TravelPost` | 4 |
| 用户资料 `UserProfile` | 3 |
| 已保存行程 `TravelPlan` | 7 |
| 操作日志 `OperationLog` | 49 |
| 旧版目的地 `Destination` | 5 |
| 旧版行程 `TripPlan` | 2 |

当前数据库中存在的主要表：

- `core_travelcity`
- `core_attraction`
- `core_userprofile`
- `core_travelplan`
- `core_travelpost`
- `core_postlike`
- `core_postfavorite`
- `core_postcomment`
- `core_operationlog`
- `authtoken_token`
- Django 自带认证与迁移表
- 旧版遗留表：`core_destination`、`core_tripplan`

### 2.3 当前已验证通过

- `backend/.venv/Scripts/python.exe manage.py check`
- `frontend/npm run build`

说明当前代码至少在“配置完整、依赖齐全、前后端能构建”的层面是成立的。

---

## 3. 仓库结构总览

```text
smart_travel/
├─ backend/
│  ├─ apps/
│  │  ├─ core/
│  │  ├─ users/
│  │  ├─ destinations/
│  │  ├─ planner/
│  │  ├─ community/
│  │  └─ backoffice/
│  ├─ scripts/
│  ├─ media/
│  ├─ smart_travel/
│  ├─ manage.py
│  └─ requirements.txt
├─ frontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ router/
│  │  ├─ services/
│  │  ├─ stores/
│  │  ├─ utils/
│  │  ├─ views/
│  │  ├─ App.vue
│  │  ├─ main.js
│  │  └─ styles.css
│  ├─ package.json
│  └─ vite.config.js
├─ cities_data_excel/
├─ crawled_city_excels/
├─ docs/
└─ README.md
```

理解这份结构时，建议用一句话记住：

- `backend/apps/core` 放“模型和基础设施”
- 其他 app 放“业务逻辑”
- `frontend/src/views` 放页面
- `frontend/src/components` 放可复用组件

---

## 4. 后端整体架构

## 4.1 总入口

### `backend/manage.py`

标准 Django 命令入口，负责启动管理命令、迁移、runserver。

### `backend/smart_travel/settings.py`

这是后端的总配置文件，关键点有：

- 注册 app：`core/users/destinations/planner/community/backoffice`
- 开启 `rest_framework` 与 `rest_framework.authtoken`
- 默认数据库为 MySQL
- 支持 `DB_ENGINE=sqlite`
- 开启 `CORS_ALLOW_ALL_ORIGINS = True`
- 认证方式：
  - `TokenAuthentication`
  - `SessionAuthentication`
- 媒体目录：
  - `MEDIA_URL = /media/`
  - `MEDIA_ROOT = backend/media`

这份配置很适合开发阶段，但不适合直接上线，原因在第 11 节会讲。

### `backend/smart_travel/urls.py`

全局路由分发：

- `/site-admin/` -> Django Admin
- `/api/` -> users
- `/api/` -> destinations
- `/api/` -> planner
- `/api/` -> community
- `/api/backoffice/` -> backoffice

另外在 `DEBUG=True` 时直接把 `MEDIA_URL` 挂出来，方便本地预览上传图片。

### `backend/smart_travel/asgi.py` / `wsgi.py`

标准部署入口，当前没有自定义逻辑。

---

## 4.2 数据模型与数据库设计

所有主模型都集中在 `backend/apps/core/models.py`。

这是本项目最重要的一份文件，因为它定义了数据库结构。

### 4.2.1 当前“主业务模型”

| 模型 | 作用 |
| --- | --- |
| `TravelCity` | 城市/区域/景区聚合对象 |
| `Attraction` | 景点明细 |
| `UserProfile` | 用户扩展资料 |
| `TravelPlan` | 用户保存的 AI 行程 |
| `TravelPost` | 社区帖子 |
| `PostLike` | 点赞关系 |
| `PostFavorite` | 收藏关系 |
| `PostComment` | 评论与回复 |
| `OperationLog` | 操作日志 |

### 4.2.2 当前“遗留模型”

| 模型 | 当前状态 |
| --- | --- |
| `Destination` | 老版目的地模型，已不再是主业务入口 |
| `TripPlan` | 老版行程模型，已被 `TravelPlan` 替代 |

这两个模型依然存在于数据库中，也依然注册了 Django Admin，但当前 API 与前端已经主要围绕 `TravelCity` / `Attraction` / `TravelPlan` 工作。

### 4.2.3 核心关系

```text
TravelCity 1 ---- n Attraction
TravelCity 1 ---- n TravelPlan
TravelCity 1 ---- n TravelPost

User 1 ---- 1 UserProfile
User 1 ---- n TravelPlan
User 1 ---- n TravelPost

TravelPost 1 ---- n PostLike
TravelPost 1 ---- n PostFavorite
TravelPost 1 ---- n PostComment
PostComment 1 ---- n PostComment(回复)
```

### 4.2.4 关键字段设计

#### `TravelCity`

承担“城市详情页”和“城市筛选列表”的主数据：

- `name`, `province`, `destination_type`
- `short_intro`, `overview`, `travel_highlights`
- `cover_image`
- `best_season`, `recommended_days`
- `average_rating`, `average_ticket`
- `attraction_count`
- `tags`
- `travel_tips`
- `is_featured`

这说明城市并不是纯行政区，而是“适合展示给用户的旅游目的地对象”。

#### `Attraction`

承担“景点详情页”和 AI 行程中的颗粒度数据：

- 属于某个 `TravelCity`
- 有地址、介绍、开放时间、票务、季节、建议游玩时长
- 有 `tags`
- 有来源文件与来源链接

这里用了唯一约束：

- `uniq_attraction_city_name`

即同一个城市里同名景点只能有一条。

#### `UserProfile`

解决 Django 默认 `auth_user` 不够用的问题：

- 昵称
- 头像链接
- 简介
- 常住城市
- 常住城市外键引用
- 偏好风格

#### `TravelPlan`

这是现在真正被前端使用的 AI 行程存储模型：

- 关联用户
- 关联城市
- 天数、预算、同行方式、兴趣
- `summary`
- `estimated_budget`
- `itinerary`，直接存 JSON

#### `TravelPost`

社区帖子主体：

- 作者
- 可选城市
- 可选景点
- 标题、正文、封面
- 标签
- 点赞数、浏览数

#### `OperationLog`

这是项目很值得讲的一个点。

项目没有只做 CRUD，还把很多动作记成日志：

- 登录
- 登出
- 更新资料
- 生成行程
- 发帖
- 点赞/收藏
- 后台增删改
- Excel 导入
- 文件上传

这让后台真正具备了“审计”味道。

---

## 4.3 `core` 模块逐文件说明

`core` 现在不是“大杂烩业务层”，而是“模型 + 基础设施 + 兼容层”。

### 真正有业务价值的文件

- `models.py`
  - 定义全部数据库模型
- `activity.py`
  - 统一写入 `OperationLog`
- `media_utils.py`
  - 上传文件校验、分类、落盘、URL 组装
- `permissions.py`
  - 自定义权限：
    - 作者或管理员可写
    - 管理员只读/可写
    - 管理员专用
- `tagging.py`
  - 统一清洗公开标签与个人偏好标签

### 兼容层文件

- `serializers.py`
- `services.py`
- `views.py`
- `urls.py`
- `importers.py`

这些文件本身不再承载新逻辑，存在意义是：

1. 说明旧版逻辑已经迁移。
2. 给历史 import 路径留缓冲。

### 管理命令

- `management/commands/import_city_excels.py`
  - 从一个目录批量导入 Excel
- `seed_demo_data.py`
  - 初始化演示用户、Token、示例帖子
- `normalize_tags.py`
  - 统一已有数据中的标签集合

### Django Admin

- `admin.py`
  - 给老版 `Destination` / `TripPlan` 和日志注册管理后台

这一点也说明：项目已经从旧模型迁移思路上前进了一步，但为了稳妥，没有把旧数据结构完全删掉。

---

## 4.4 `users` 模块逐文件说明

`users` 负责认证、个人资料和文件上传。

### `users/services.py`

职责：

- `ensure_user_profile()`
  - 确保每个用户都有 `UserProfile`
- `assign_home_city()`
  - 根据城市名或城市对象绑定常住城市
- `serialize_user()`
  - 输出给前端的统一用户结构

这是一个典型“把重复逻辑抽出”的服务层。

### `users/serializers.py`

职责：

- 注册参数校验
- 登录参数校验
- 个人资料序列化
- 偏好风格标准化

### `users/views.py`

提供接口：

- `RegisterAPIView`
- `LoginAPIView`
- `LogoutAPIView`
- `MeAPIView`
- `ProfileAPIView`
- `MediaUploadAPIView`

设计亮点：

1. 登录注册成功后直接返回 Token 和用户摘要。
2. 更新资料会写操作日志。
3. 上传文件会限制类型和大小。

### `users/urls.py`

挂出：

- `/api/auth/register/`
- `/api/auth/login/`
- `/api/auth/logout/`
- `/api/auth/me/`
- `/api/profile/me/`
- `/api/uploads/`

### `users/admin.py`

把 `UserProfile` 挂到 Django Admin。

---

## 4.5 `destinations` 模块逐文件说明

这是项目里最像“业务中台”的模块。

### `destinations/serializers.py`

负责：

- 城市列表/详情输出
- 景点列表/详情输出
- 嵌套关系输出

### `destinations/views.py`

提供：

- `GET /api/overview/`
- `GET /api/cities/`
- `GET /api/cities/{id}/`
- `GET /api/cities/recommend/`
- `GET /api/attractions/`
- `GET /api/attractions/{id}/`

支持的筛选条件包括：

- 关键词
- 省份
- 标签
- 城市 ID
- limit

### `destinations/home_recommendations.py`

这是首页个性化推荐的真正实现文件。

它会根据：

- 用户是否登录
- 用户常住城市
- 用户偏好风格

重新排序：

- 首页推荐城市
- 首页景点卡片
- 最新帖子文案

也就是说，首页并不是死列表，而是“有轻度个性化”的。

### `destinations/services.py`

这是“数据清洗 + 数据归纳”模块，主要服务导入过程。

它负责：

- 清洗文本
- 解析门票字段
- 识别省份
- 推断目的地类型
- 推断标签
- 计算城市评分/推荐天数/平均票价/简介

这部分非常适合答辩时讲，因为它说明你不是把 Excel 生搬硬套进数据库，而是做了“二次整理”。

### `destinations/importers.py`

这是 Excel 入库的关键文件。

工作流程：

1. 打开工作簿
2. 检查表头是否匹配预期模板
3. 生成城市默认字段
4. `update_or_create` 城市
5. 逐行 `update_or_create` 景点
6. 可选删除当前工作簿已不存在的旧景点
7. 调用 `compute_city_profile()` 回填城市聚合字段

### `destinations/admin.py`

在 Django Admin 中管理：

- `TravelCity`
- `Attraction`

### `destinations/apps.py`

仅定义 AppConfig，无业务逻辑。

---

## 4.6 `planner` 模块逐文件说明

`planner` 是“AI 行程生成 + 行程保存”的模块。

### `planner/services.py`

这是项目里逻辑最密集的一层之一。

它做了两套规划模式：

#### 1. 规则规划

基于以下信息排序城市与景点：

- 兴趣标签
- 城市标签
- 景点评分
- 门票情况
- 推荐季节

然后按每天最多 3 个景点拆成：

- 上午
- 下午
- 夜晚

#### 2. LLM 规划

如果环境变量存在：

- `LLM_API_KEY` 或 `OPENAI_API_KEY`
- `LLM_API_MODEL` 或 `OPENAI_MODEL`

就会走一个 OpenAI-compatible 的 `/chat/completions` 调用。

它会：

1. 从当前城市挑出一个候选景点池
2. 把城市、景点、用户偏好打成 JSON prompt
3. 要求模型只从给定景点里选
4. 解析模型返回 JSON
5. 转成前端可直接渲染的 itinerary

如果调用失败，会自动降级回规则规划。

这是一种很实用的学生项目做法：

- 有 AI
- 但不把系统生死绑在 AI 上

### `planner/views.py`

提供：

- `POST /api/planner/generate/`
- `GET/POST /api/plans/`

逻辑：

- 前台提交条件
- 生成行程
- 如用户已登录且勾选 `save_plan`
  - 则写入 `TravelPlan`

### `planner/serializers.py`

负责已保存行程输出。

### `planner/admin.py`

将 `TravelPlan` 注册到 Django Admin。

---

## 4.7 `community` 模块逐文件说明

这个模块承担社区信息流。

### `community/serializers.py`

拆成三类：

- 帖子列表
- 帖子详情
- 评论

还额外计算：

- 当前用户是否已点赞
- 当前用户是否已收藏
- 评论数
- 收藏数

### `community/services.py`

只有一个核心辅助函数：

- `refresh_post_counters()`

即：点赞后刷新帖子点赞数。

### `community/views.py`

主入口是 `TravelPostViewSet`，支持：

- 帖子列表
- 帖子详情
- 发帖
- 点赞
- 收藏
- 评论
- 查看收藏帖子

权限设计：

- 列表、详情：游客可看
- 发帖、点赞、收藏、评论：必须登录
- 修改/删除：作者或管理员

### `community/admin.py`

注册：

- `TravelPost`
- `PostComment`
- `PostLike`

---

## 4.8 `backoffice` 模块逐文件说明

这是后台管理 API，不是 Django Admin，而是给 Vue 后台页用的接口层。

### `backoffice/views.py`

主要能力：

- `summary`
  - 统计数字、热门城市、最新帖子、最近日志
- `users`
  - 用户筛选、编辑、删除
- `cities`
  - 城市 CRUD
- `attractions`
  - 景点 CRUD
- `posts`
  - 帖子筛选、删除
- `logs`
  - 日志查询
- `import-excels`
  - 本地目录导入 Excel
- `import-excels/upload`
  - 浏览器上传 Excel 后导入

### `backoffice/serializers.py`

对应后台页所需的数据结构：

- `AdminUserSerializer`
- `TravelCityAdminSerializer`
- `TravelPostAdminSerializer`
- `OperationLogSerializer`

### `backoffice/urls.py`

统一挂在 `/api/backoffice/` 下。

### `backoffice/admin.py`

只是改了 Django Admin 标题，不承载业务逻辑。

---

## 4.9 爬虫与数据导入

### `backend/scripts/crawl_ctrip_city_sights.py`

这是一个很关键的“数据生产脚本”。

它做的事情：

1. 打开携程城市景点列表页
2. 从页面里的 `__NEXT_DATA__` 提取 JSON
3. 解析景点卡片
4. 逐个进入景点详情页
5. 抽取：
   - 名字
   - 链接
   - 地址
   - 介绍
   - 开放时间
   - 图片
   - 评分
   - 游玩时间
   - 门票
   - 小贴士
6. 写成项目兼容的 Excel 模板
7. 可选直接导入 Django/MySQL

这个脚本和 `destinations/importers.py` 一起，构成了项目的数据入口。

### 数据入口一共有两条

#### 方式 A：已有 Excel

目录：

- `cities_data_excel/`

#### 方式 B：爬虫输出 Excel

目录：

- `crawled_city_excels/`

### 导入后的处理链

```text
Excel / 爬虫输出
    -> destinations.importers.import_excel_file()
    -> TravelCity / Attraction update_or_create
    -> compute_city_profile()
    -> MySQL
    -> API
    -> Vue 页面
```

---

## 5. 后端源码速查表

如果你想快速按文件找职责，可以看这一节。

### 5.1 后端基础层

| 文件 | 作用 |
| --- | --- |
| `backend/manage.py` | Django 命令入口 |
| `backend/requirements.txt` | Python 依赖 |
| `backend/smart_travel/settings.py` | 项目总配置 |
| `backend/smart_travel/urls.py` | 项目总路由 |
| `backend/smart_travel/asgi.py` | ASGI 入口 |
| `backend/smart_travel/wsgi.py` | WSGI 入口 |
| `backend/scripts/crawl_ctrip_city_sights.py` | 携程景点爬虫 + Excel 生成 |

### 5.2 `apps/core`

| 文件 | 作用 |
| --- | --- |
| `models.py` | 全部数据库模型 |
| `activity.py` | 操作日志写入 |
| `media_utils.py` | 本地媒体上传保存 |
| `permissions.py` | 自定义权限类 |
| `tagging.py` | 标签标准化 |
| `importers.py` | 导入兼容转发层 |
| `serializers.py` | 兼容层 |
| `services.py` | 兼容层 |
| `views.py` | 兼容层 |
| `urls.py` | 兼容层 |
| `admin.py` | 老版模型与日志的 Django Admin |
| `management/commands/import_city_excels.py` | 目录导入 |
| `management/commands/seed_demo_data.py` | 演示数据 |
| `management/commands/normalize_tags.py` | 标签归一化 |

### 5.3 `apps/users`

| 文件 | 作用 |
| --- | --- |
| `serializers.py` | 注册、登录、资料序列化 |
| `services.py` | 用户资料补全与序列化 |
| `views.py` | 认证、资料、上传接口 |
| `urls.py` | 用户相关 API 路由 |
| `admin.py` | UserProfile 后台管理 |

### 5.4 `apps/destinations`

| 文件 | 作用 |
| --- | --- |
| `serializers.py` | 城市/景点序列化 |
| `views.py` | 首页、城市、景点接口 |
| `services.py` | 数据清洗、推断、聚合 |
| `home_recommendations.py` | 首页个性化推荐 |
| `importers.py` | Excel 导入 |
| `urls.py` | 目的地 API 路由 |
| `admin.py` | 城市与景点 Django Admin |

### 5.5 `apps/planner`

| 文件 | 作用 |
| --- | --- |
| `services.py` | 规则规划 + LLM 规划 |
| `views.py` | 生成行程与保存行程 |
| `serializers.py` | 已保存行程序列化 |
| `urls.py` | 行程 API 路由 |
| `admin.py` | TravelPlan Django Admin |

### 5.6 `apps/community`

| 文件 | 作用 |
| --- | --- |
| `serializers.py` | 帖子/评论序列化 |
| `services.py` | 帖子计数刷新 |
| `views.py` | 帖子、点赞、收藏、评论 |
| `urls.py` | 社区 API 路由 |
| `admin.py` | 社区模型 Django Admin |

### 5.7 `apps/backoffice`

| 文件 | 作用 |
| --- | --- |
| `serializers.py` | 后台管理序列化 |
| `views.py` | 后台工作台与 CRUD API |
| `urls.py` | 后台 API 路由 |
| `admin.py` | Django Admin 标题定制 |

补充说明：

- 各目录里的 `apps.py` 只是 AppConfig。
- 各目录里的 `__init__.py` 只是包标记。

---

## 6. API 总表

## 6.1 认证与个人资料

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/register/` | 注册并直接返回 Token |
| POST | `/api/auth/login/` | 登录并返回 Token |
| POST | `/api/auth/logout/` | 退出并删除当前 Token |
| GET | `/api/auth/me/` | 获取当前用户摘要 |
| GET | `/api/profile/me/` | 获取个人主页资料 |
| PATCH | `/api/profile/me/` | 更新个人主页资料 |
| POST | `/api/uploads/` | 上传头像、帖子封面、景点图、Excel 等文件 |

## 6.2 首页 / 城市 / 景点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/overview/` | 首页总览数据 |
| GET | `/api/cities/` | 城市列表 |
| GET | `/api/cities/{id}/` | 城市详情，带景点列表 |
| GET | `/api/cities/recommend/` | 根据兴趣/预算/季节推荐城市 |
| GET | `/api/attractions/` | 景点列表 |
| GET | `/api/attractions/{id}/` | 景点详情 |

## 6.3 AI 行程

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/planner/generate/` | 生成 AI 行程 |
| GET | `/api/plans/` | 查看我的已保存行程 |
| POST | `/api/plans/` | 保存行程 |

## 6.4 社区

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/posts/` | 帖子流 |
| GET | `/api/posts/{id}/` | 帖子详情 |
| POST | `/api/posts/` | 发帖 |
| GET | `/api/posts/favorites/` | 我收藏的帖子 |
| POST | `/api/posts/{id}/like/` | 点赞 / 取消点赞 |
| POST | `/api/posts/{id}/favorite/` | 收藏 / 取消收藏 |
| POST | `/api/posts/{id}/comment/` | 评论帖子 |

## 6.5 后台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/backoffice/summary/` | 工作台总览 |
| GET/PUT/PATCH/DELETE | `/api/backoffice/users/{id}/` | 用户管理 |
| GET/POST/PUT/DELETE | `/api/backoffice/cities/` | 城市管理 |
| GET/POST/PUT/DELETE | `/api/backoffice/attractions/` | 景点管理 |
| GET/DELETE | `/api/backoffice/posts/` | 帖子管理 |
| GET | `/api/backoffice/logs/` | 日志列表 |
| POST | `/api/backoffice/import-excels/` | 按目录导入 Excel |
| POST | `/api/backoffice/import-excels/upload/` | 上传 Excel 并导入 |

---

## 7. 前端整体架构

## 7.1 前端入口层

### `frontend/index.html`

Vite 的 HTML 宿主页，挂载点是 `#app`。

### `frontend/src/main.js`

前端启动顺序：

1. 读取本地 token
2. 如果 token 存在但用户对象为空，则调用 `/api/auth/me/`
3. 挂载 Vue 应用

### `frontend/src/App.vue`

它不是业务页面，而是总壳子。

分两种布局：

1. 用户端布局
   - 顶部导航
   - 页面切换动画
   - 右下角回顶部/回首页按钮

2. 后台布局
   - 左侧边栏
   - 顶部后台头部
   - 中间业务区域

### `frontend/src/router/index.js`

定义了全部前端路由与守卫：

- 普通路由：首页、城市、景点、社区、登录、注册、个人主页
- 管理员路由：`/backoffice`

守卫规则：

- 需要登录但没 token -> 跳登录页
- 登录后访问 guestOnly 页面 -> 跳走
- 非管理员访问后台 -> 回首页

### `frontend/src/services/api.js`

这是前端调用后端的唯一 API 封装层。

特点：

- Axios 实例统一 `baseURL: /api`
- 请求拦截器自动带上 `Token xxx`
- 响应拦截器遇到 401 自动清空登录态
- 所有接口都有对应函数，调用点很清晰

### `frontend/src/stores/auth.js`

不是 Pinia，而是一个轻量 reactive store。

负责：

- 从 `localStorage` 读取 token / user
- 保存登录态
- 清除登录态

### `frontend/src/styles.css`

全局设计系统。

它统一定义了：

- 颜色变量
- 字体变量
- 通用卡片、按钮、栅格、表单、后台布局样式
- 页面转场动画

你可以把它理解成这个项目的“全局 UI 框架”。

---

## 7.2 页面层逐一说明

### `views/HomeView.vue`

首页，负责组合：

- 轮播城市
- 省份入口
- 景点推荐
- 城市推荐
- 最新帖子

调用接口：

- `getOverview()`
- `getCities({ limit: 500 })`

### `views/CityListView.vue`

城市列表页。

能力：

- 关键词搜索
- 省份筛选
- 标签筛选
- 懒加载继续展示

### `views/CityDetailView.vue`

城市详情页。

页面结构：

- 左侧城市总览
- 右侧景点导览台
- 下方核心景点卡片

它本质上是“城市 -> 景点”的二级入口页。

### `views/AttractionListView.vue`

景点总览页。

支持：

- 关键词
- 省份
- 城市
- 标签

### `views/AttractionDetailView.vue`

景点详情页。

承担：

- 展示结构化信息
- 回到所属城市
- 跳 AI 行程
- 关联社区内容

### `views/PlannerView.vue`

AI 行程页。

功能：

- 选择目标城市与出发城市
- 选择天数、季节、预算、同行方式、兴趣
- 调用生成接口
- 展示预算拆分、推荐城市、必去景点、逐日行程
- 可选保存行程

### `views/CommunityView.vue`

社区首页。

布局：

- 左：筛选
- 中：信息流
- 右：发帖表单

### `views/PostDetailView.vue`

帖子详情页。

能力：

- 帖子正文
- 点赞 / 收藏
- 评论与回复展示
- 跳转关联城市或景点

### `views/LoginView.vue`

登录页，登录后根据是否管理员跳转：

- 普通用户 -> `/`
- 管理员 -> `/backoffice`

### `views/RegisterView.vue`

注册页，注册成功后自动写入登录态并跳首页。

### `views/ProfileView.vue`

个人主页。

能力：

- 上传头像
- 修改昵称、简介、常住城市、偏好风格
- 查看我的收藏
- 查看我的帖子

### `views/AdminView.vue`

单文件后台页面。

这是前端里体量最大的一份文件，承担：

- 总览工作台
- Excel 导入
- 用户管理
- 城市管理
- 景点管理
- 帖子管理
- 日志查看

它当前已经能用，但未来最适合继续拆分。

---

## 7.3 组件层逐一说明

## 通用组件

| 文件 | 作用 |
| --- | --- |
| `AppHeader.vue` | 用户端顶部导航，负责登录态展示与退出 |
| `AppLogo.vue` | 项目 Logo 组件 |
| `SectionHeader.vue` | 各区块统一标题头 |
| `PageBackButton.vue` | 通用返回按钮 |
| `ScrollTopButton.vue` | 右下角回顶部/回首页浮动按钮 |
| `FileUploadField.vue` | 通用上传组件，内部直接调 `/api/uploads/` |

## 卡片组件

| 文件 | 作用 |
| --- | --- |
| `CityCard.vue` | 城市卡片 |
| `AttractionCard.vue` | 景点卡片，可展开简介 |
| `PostCard.vue` | 通用帖子卡片，支持点赞/收藏 |
| `CommunityFeedCard.vue` | 社区信息流风格帖子卡片 |
| `StatCard.vue` | 简单统计卡片，当前未被页面引用 |

## 首页/认证/后台专用组件

| 文件 | 作用 |
| --- | --- |
| `home/HomeHeroCarousel.vue` | 首页轮播 |
| `auth/AuthShowcase.vue` | 登录注册页左侧展示区 |
| `backoffice/BackofficeHeader.vue` | 后台顶部头部 |
| `backoffice/BackofficeSidebar.vue` | 后台左侧导航 |
| `backoffice/DashboardBarChart.vue` | 后台条形图 |
| `backoffice/DashboardDonutChart.vue` | 后台环图 |

## 地图组件

| 文件 | 当前状态 |
| --- | --- |
| `maps/ChinaMapBoard.vue` | 已写好，但当前未接入页面 |
| `maps/ProvinceCityMap.vue` | 已写好，但当前未接入页面 |
| `maps/CityScenicMap.vue` | 已写好，但当前未接入页面 |

这些组件和 `utils/mapData.js` 说明你原本考虑过“地图式浏览”，但现阶段页面已经改成更偏图文卡片式导览。

---

## 7.4 工具层

### `utils/mapData.js`

作用：

- 省份名标准化
- 省份布局坐标
- 城市节点位置
- 景点节点位置
- 标签去重

当前实际被使用的函数主要是：

- `buildProvinceStats`
- `dedupeTags`
- `normalizeProvince`

### `utils/profileOptions.js`

定义个人主页可选偏好风格列表。

---

## 8. 前端源码速查表

### 8.1 前端基础层

| 文件 | 作用 |
| --- | --- |
| `frontend/package.json` | npm 依赖与脚本 |
| `frontend/vite.config.js` | Vite 配置，开发期把 `/api` 代理到 `127.0.0.1:8000` |
| `frontend/index.html` | 挂载页面 |
| `frontend/src/main.js` | 启动入口 |
| `frontend/src/App.vue` | 前台/后台双布局总壳 |
| `frontend/src/styles.css` | 全局样式系统 |
| `frontend/src/router/index.js` | 路由与守卫 |
| `frontend/src/services/api.js` | 全部 API 封装 |
| `frontend/src/stores/auth.js` | 登录态本地存储 |

### 8.2 页面文件

| 文件 | 作用 |
| --- | --- |
| `HomeView.vue` | 首页 |
| `CityListView.vue` | 城市列表 |
| `CityDetailView.vue` | 城市详情 |
| `AttractionListView.vue` | 景点列表 |
| `AttractionDetailView.vue` | 景点详情 |
| `PlannerView.vue` | AI 行程 |
| `CommunityView.vue` | 社区首页 |
| `PostDetailView.vue` | 帖子详情 |
| `LoginView.vue` | 登录 |
| `RegisterView.vue` | 注册 |
| `ProfileView.vue` | 个人主页 |
| `AdminView.vue` | 后台工作台 |

### 8.3 组件文件

除地图与 `StatCard.vue` 外，其余组件都已经接入页面。

---

## 9. 数据流与业务流

## 9.1 数据生产流

```text
携程网页 / 本地Excel
    -> crawl_ctrip_city_sights.py
    -> 统一Excel模板
    -> import_excel_file / import_excel_directory
    -> TravelCity / Attraction
    -> 城市聚合字段自动计算
    -> MySQL
```

## 9.2 页面访问流

```text
Vue 页面
    -> services/api.js
    -> Django APIView / ViewSet
    -> serializer / service
    -> ORM
    -> MySQL
    -> JSON
    -> Vue 渲染
```

## 9.3 上传流

```text
前端 FileUploadField
    -> /api/uploads/
    -> media_utils.save_uploaded_file()
    -> backend/media/分类目录/
    -> 返回可访问 URL
    -> URL 保存到头像/封面/景点图字段
```

## 9.4 AI 行程流

```text
前端 Planner 表单
    -> /api/planner/generate/
    -> build_ai_plan()
        -> 尝试目标城市匹配
        -> 推荐城市
        -> 选景点
        -> 如果配置了 LLM 就调用大模型
        -> 否则走规则生成
    -> 返回 itinerary JSON
    -> 前端按 Day/上午/下午/夜晚 展示
```

---

## 10. 这个项目当前阶段已经完成得比较好的地方

### 10.1 架构层面

- 没有把所有接口都堆在一个 app 里。
- 模型层与业务层已经分开。
- 后台 API 和前台 API 也已经分层。

### 10.2 数据层面

- 不只是展示静态假数据。
- 已经做了 Excel 导入。
- 已经做了真实网页爬虫。
- 已经做了标签与城市聚合计算。

### 10.3 交互层面

- 前台链路完整：浏览 -> 详情 -> 规划 -> 社区 -> 个人主页
- 后台链路完整：总览 -> 用户 -> 城市 -> 景点 -> 帖子 -> 日志

### 10.4 工程层面

- 有日志
- 有文件上传
- 有演示数据命令
- 有 build/check 验证

如果是课程项目或毕业设计，这已经不是“只有页面效果”的项目，而是“业务链路较完整的系统”。

---

## 11. 当前明显存在的问题

这一节是最适合你下一阶段继续做的地方。

## 11.1 配置与安全问题

### 问题 1：敏感信息硬编码

当前 `settings.py` 里直接写了：

- `SECRET_KEY`
- `DEBUG = True`
- `ALLOWED_HOSTS = ["*"]`
- MySQL 账号密码

这在开发阶段可以接受，但上线不行。

### 问题 2：媒体仍保存在本地磁盘

现在头像、帖子封面、景点图、Excel 上传都在：

- `backend/media/`

这意味着：

- 多机部署不方便
- 容器重建有丢失风险
- CDN 分发能力弱

### 问题 3：CORS 全开放

当前：

- `CORS_ALLOW_ALL_ORIGINS = True`

开发期方便，生产期风险高。

---

## 11.2 架构与代码问题

### 问题 4：存在旧模型与旧表

当前数据库里仍有：

- `core_destination`
- `core_tripplan`

对应模型：

- `Destination`
- `TripPlan`

说明项目正处在“新旧并存”阶段。

### 问题 5：`AdminView.vue` 过大

后台页现在是单文件承载所有 tab。

问题：

- 文件太长
- 状态太多
- 后续维护成本会快速升高

### 问题 6：有一批前端组件未接入

当前未发现被页面引用：

- `StatCard.vue`
- `maps/ChinaMapBoard.vue`
- `maps/ProvinceCityMap.vue`
- `maps/CityScenicMap.vue`

这类文件要么继续接入，要么明确归档为预研代码。

### 问题 7：默认路径写死在个人电脑目录

例如：

- `C:/Users/YT-yuntian/Desktop/cities_data_excel`

这会导致项目移交、部署、多人协作时很别扭。

---

## 11.3 数据质量问题

### 问题 8：演示帖子数据存在错位

我核对数据库时发现有帖子标题和关联城市不完全匹配，例如：

- 标题看起来在写成都，但城市字段落在上海

这不是系统结构问题，而是演示数据问题。

### 问题 9：列表接口缺少真正的分页

现在常见做法是：

- 前端一次拉 80、120、500 条
- 再在前端懒加载展示

这对学生项目可以，但数据再涨就不适合。

---

## 11.4 测试与运维问题

### 问题 10：没有自动化测试

当前能看到的是：

- `manage.py check`
- `npm run build`

但还没有：

- 后端接口测试
- 导入脚本测试
- 前端页面交互测试

### 问题 11：没有 CI/CD

当前发布仍是手工式：

- 手工 build
- 手工 runserver
- 手工导入

---

## 12. 改进建议：按优先级排序

下面我不只说“能做什么”，还会说“为什么值得做”和“应落到哪里”。

## 12.1 第一优先级：先把配置安全化

### 建议

把以下内容改为环境变量：

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_*`
- `LLM_API_*`
- OSS 配置
- 上传目录配置

### 为什么

Django 官方部署清单明确强调：

- 生产环境不要开 `DEBUG`
- `SECRET_KEY` 不要硬编码
- `ALLOWED_HOSTS` 需要正确配置
- 数据库密码要像 `SECRET_KEY` 一样保护

### 落地位置

- `backend/smart_travel/settings.py`
- 新增 `.env.example`
- 新增 `settings_dev.py` / `settings_prod.py` 或环境变量分支

---

## 12.2 第二优先级：把上传文件迁到 OSS

### 为什么值得做

阿里云 OSS 官方资料显示，它本身就适合：

- 存储任意类型数据
- 做生命周期管理
- 做权限控制
- 做日志审计
- 和 CDN 组合做更快的内容分发

这非常适合你这个项目里的：

- 头像
- 城市封面
- 景点图片
- 帖子封面
- Excel 上传文件

### 你这个项目最适合怎么改

#### 当前做法

- 上传文件
- 保存到 `backend/media/`
- 数据库里直接存完整 URL

#### 更推荐的做法

1. Django 只负责签名、上传策略和对象 key 生成
2. 文件直接上传到 OSS
3. 数据库只保存对象 key 或 CDN URL
4. 前端统一从 CDN 域名读资源

### 推荐改造方案

#### 方案 A：后端转存 OSS

流程最接近现在的实现：

- 前端仍然发到 `/api/uploads/`
- Django 收到后上传到 OSS
- 返回 OSS/CDN URL

优点：

- 改动小
- 前端几乎不用重写

#### 方案 B：前端直传 OSS

更适合后期：

- 后端生成临时上传凭证
- 前端直接上传 OSS
- 上传成功后回写对象 key

优点：

- 节省 Django 带宽
- 大文件上传更稳

### 落地位置

- `backend/apps/core/media_utils.py`
- `backend/apps/users/views.py` 中的 `MediaUploadAPIView`
- `frontend/src/components/FileUploadField.vue`

### 技术实现建议

- 保留现有接口名不变
- 先把实现从“落本地”换成“传 OSS”
- 再逐步把“完整 URL 存库”改成“对象 key 存库”

---

## 12.3 第三优先级：引入地图与路线 API

### 推荐：高德开放平台 Web 服务 API

根据高德官方文档，当前可直接使用：

- 地理编码 / 逆地理编码
- 步行路径规划
- 公交路径规划
- 驾车路径规划

### 对这个项目的具体价值

#### 价值 1：清洗已有景点地址

现在 `Attraction.address` 基本是文本。

可以新增：

- `longitude`
- `latitude`
- `adcode`

流程：

1. 导入 Excel 后
2. 用地理编码 API 把地址转经纬度
3. 把坐标存表

这样后面很多功能都能做。

#### 价值 2：城市详情页/景点详情页恢复地图能力

你已经写了三份地图组件，但现在还没接真实地图服务。

如果接入高德：

- 城市详情页可以显示景点点位
- 景点详情页可以显示地理位置
- 行程页可以显示路线串联

#### 价值 3：AI 行程不只是“选景点”，还能“算动线”

当前 `build_ai_plan()` 已经输出：

- `transport_tip`

但这还是文案级建议。

接入高德路线规划后，可以让每天行程真正有：

- 步行时长
- 公交方案
- 驾车方案
- 总距离

### 最适合接入的位置

- 数据补全：`backend/apps/destinations/importers.py`
- 城市详情接口：`backend/apps/destinations/views.py`
- AI 行程：`backend/apps/planner/services.py`
- 前端地图组件：`frontend/src/components/maps/*.vue`

---

## 12.4 第四优先级：引入天气 API

### 推荐：和风天气开发服务

根据和风天气官方文档，目前能提供：

- GeoAPI 城市/地点搜索
- 实时天气
- 每日天气预报
- 逐小时天气预报
- 分钟级降水
- 天气预警
- 天气指数
- 空气质量

### 对这个项目的具体价值

#### 价值 1：城市详情页更真实

可以在城市详情页增加：

- 当前天气
- 未来 3 天/7 天天气
- 穿衣/紫外线/降雨提示

#### 价值 2：AI 行程能按天气调整

例如：

- 下雨天减少户外景点
- 高温天把室内馆安排在下午
- 夜间降雨则弱化夜景行程

#### 价值 3：提升“建议季节”之外的实时性

现在系统有：

- `best_season`

但它是静态字段。

天气 API 能补上“实时旅行条件”。

### 落地位置

- 新建 `backend/apps/destinations/weather_services.py`
- 城市详情接口增加 weather block
- `PlannerGenerateAPIView` 输出天气提示
- `PlannerView.vue` / `CityDetailView.vue` 展示天气卡片

---

## 12.5 第五优先级：把后台继续拆模块

### 当前问题

`frontend/src/views/AdminView.vue` 已经承担太多职责。

### 推荐拆法

拆成：

- `views/admin/AdminOverviewView.vue`
- `views/admin/AdminUsersView.vue`
- `views/admin/AdminCitiesView.vue`
- `views/admin/AdminAttractionsView.vue`
- `views/admin/AdminPostsView.vue`
- `views/admin/AdminLogsView.vue`

再让 `/backoffice` 下面走子路由。

### 收益

- 组件粒度更合理
- 逻辑更容易维护
- 后台页更像正式系统

---

## 12.6 第六优先级：补分页、缓存、搜索

### 分页

当前很多接口靠 `limit`，建议改成 DRF 标准分页：

- `page`
- `page_size`
- `count`
- `next`
- `previous`

### 缓存

适合缓存的接口：

- `/api/overview/`
- `/api/cities/`
- `/api/attractions/`

可以引入 Redis 做：

- 热门列表缓存
- 首页推荐缓存
- 城市详情缓存

### 搜索

当前搜索主要是 `icontains`。

下一阶段可选：

- MySQL 全文索引
- Elasticsearch / OpenSearch

学生项目阶段先上 MySQL 全文就够了。

---

## 12.7 第七优先级：把部署方案定型

这里我给你一个最实用的上线方案。

### 推荐的生产部署结构

```text
浏览器
  -> Nginx
      -> Vue dist 静态文件
      -> Django API
          -> Gunicorn / Uvicorn
          -> MySQL
          -> Redis
          -> OSS
```

### 为什么这样配

- Vue 打包后就是纯静态文件，Nginx 很适合托管
- Django 专门负责 API
- MySQL 存结构化业务数据
- Redis 存缓存和未来的异步任务状态
- OSS 存媒体文件

### Django 上线前至少要做的事情

1. `DEBUG=False`
2. 配置 `ALLOWED_HOSTS`
3. 强制 HTTPS
4. 设置安全 Cookie
5. 不再使用 `manage.py runserver`
6. 正确处理静态文件和媒体文件

### 前端上线方式

有两种都行：

#### 方式 A：Nginx 直接托管 `frontend/dist`

适合和 Django 放同一台机器。

#### 方式 B：前端静态资源放 OSS + CDN

更适合后期：

- 页面更快
- 静态资源更稳定
- 可把 API 与前端完全分离

---

## 13. 如果按“下一个版本”继续做，建议顺序

### 第一阶段：工程收口

1. `.env` 化配置
2. 把默认硬编码目录改成环境变量
3. 修复演示数据错位
4. 增加 `manage.py check --deploy`

### 第二阶段：存储与上线

1. OSS 替换本地媒体
2. Nginx + Django 部署
3. 前端静态资源独立托管
4. HTTPS 与域名

### 第三阶段：数据增强

1. 高德地理编码补全景点坐标
2. 高德路线规划接入 AI 行程
3. 和风天气接入城市详情与行程页

### 第四阶段：架构增强

1. 后台拆子路由
2. 接口加分页
3. Redis 缓存
4. 自动化测试

---

## 14. 最后给你的项目结论

如果以“当前阶段已经可以了”为前提，这个项目确实已经达到了一个比较完整的节点：

- 有真实数据
- 有真实数据库
- 有前后端联调
- 有 AI 功能
- 有社区
- 有后台
- 有导入链路
- 有上传能力

它现在最缺的，不是再加一个花哨页面，而是把“工程完成度”往上推一步：

- 配置安全化
- 存储云化
- 部署规范化
- 数据实时化
- 页面与后台继续模块化

只要把第 12 节里的前 3 到 5 项做掉，这个项目就会从“完成的课程项目”升级成“可公开演示、可部署上线、可继续扩展的作品”。

---

## 15. 外部方案参考

以下建议我已经按 2026-03-23 的官方资料核对过：

- 阿里云 OSS 产品页：<https://cn.aliyun.com/product/oss?from_alibabacloud=>
- 阿里云 OSS Python SDK 文档：<https://help.aliyun.com/zh/oss/developer-reference/python-sdk-v1/>
- 阿里云 OSS Python SDK 初始化：<https://help.aliyun.com/zh/oss/developer-reference/initialization-2>
- 阿里云 OSS 上传方式说明：<https://help.aliyun.com/zh/oss/developer-reference/upload-objects-2/>
- 高德地理/逆地理编码：<https://lbs.amap.com/api/webservice/guide/api/georegeo>
- 高德路径规划：<https://lbs.amap.com/api/webservice/guide/api/direction>
- 和风天气开发文档：<https://dev.qweather.com/docs/>
- Django 官方部署清单：<https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/>
- Django 官方静态文件部署：<https://docs.djangoproject.com/en/5.1/howto/static-files/deployment/>

