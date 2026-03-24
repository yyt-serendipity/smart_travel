<template>
  <section class="page admin-page">
    <p v-if="adminMessage" class="muted status-message">{{ adminMessage }}</p>

    <article v-if="currentTab === 'overview'" class="card section-shell admin-command-center">
      <div class="admin-command-row">
        <div class="admin-command-copy">
          <span class="eyebrow">Workbench</span>
          <h2 class="section-title">企业级数据工作台</h2>
          <p class="section-description">右侧只保留当前导航对应的模块内容。总览负责承接统计、导入、系统状态和日志概览，其他能力都从左侧导航单独进入。</p>
        </div>

        <div class="admin-command-actions">
          <button class="btn btn-secondary" type="button" @click="refreshAll">刷新工作台</button>
          <button class="btn btn-primary" type="button" @click="switchTab('users')">进入用户管理</button>
        </div>
      </div>

      <div class="admin-workbench-grid">
        <div class="admin-workbench-main">
          <div class="metric-grid admin-metric-grid">
            <div v-for="card in kpiCards" :key="card.label" class="card stat-card admin-kpi-card">
              <span class="muted">{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <span class="stat-delta">{{ card.caption }}</span>
            </div>
          </div>

          <div class="admin-chart-grid">
            <DashboardBarChart
              title="城市景点覆盖"
              description="按景点数量排序，快速看内容资产最完整的城市。"
              :items="topCityChartItems"
            />
            <DashboardDonutChart
              title="平台内容结构"
              description="城市、景点、帖子和评论在当前系统中的分布。"
              :items="contentComposition"
            />
          </div>
        </div>

        <div class="admin-workbench-side">
          <article class="card admin-side-panel">
            <div class="title-row compact-row">
              <div>
                <strong>系统状态</strong>
                <p class="muted">工作台运行和运营状态</p>
              </div>
              <span class="pill">Live</span>
            </div>
            <div class="grid" style="margin-top: 16px">
              <div v-for="item in systemSignals" :key="item.label" class="timeline-item admin-signal-item">
                <div class="title-row compact-row">
                  <strong>{{ item.label }}</strong>
                  <span class="pill">{{ item.state }}</span>
                </div>
                <p class="muted">{{ item.description }}</p>
              </div>
            </div>
          </article>

          <article class="card admin-side-panel">
            <div class="title-row compact-row">
              <div>
                <strong>最近操作</strong>
                <p class="muted">用于快速确认后台近期行为</p>
              </div>
              <button class="btn btn-secondary" type="button" @click="switchTab('logs')">全部日志</button>
            </div>
            <div class="grid" style="margin-top: 16px">
              <div v-for="log in recentLogs" :key="log.id" class="timeline-item admin-log-compact">
                <strong>{{ log.action }}</strong>
                <p class="muted">{{ log.nickname || log.username || "匿名" }} · {{ log.target_name || log.request_path }}</p>
              </div>
            </div>
          </article>
        </div>
      </div>

    </article>

    <article v-if="currentTab === 'overview'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="运营总览" description="把数据导入、任务提醒和日志审计收成一个企业工作台总览。" />
        <span class="pill">Overview</span>
      </div>

      <div class="admin-overview-grid" style="margin-top: 24px">
        <article class="card admin-panel-block">
          <div class="title-row compact-row">
            <div>
              <strong>Excel 文件导入</strong>
              <p class="muted">支持浏览器批量上传工作簿并直接入库。</p>
            </div>
            <span class="pill">.xlsx</span>
          </div>

          <form class="grid" style="margin-top: 18px" @submit.prevent="handleImportFiles">
            <div class="field">
              <label for="excelFiles">上传 Excel 文件</label>
              <input id="excelFiles" type="file" accept=".xlsx" multiple @change="handleExcelChange" />
            </div>
            <label class="checkbox-row">
              <input v-model="importForm.overwrite" type="checkbox" />
              <span>覆盖工作簿中已移除的景点</span>
            </label>
            <div class="action-row">
              <button class="btn btn-primary" type="submit" :disabled="!excelFiles.length">上传并导入</button>
            </div>
          </form>

          <div v-if="excelFiles.length" class="chip-row" style="margin-top: 16px">
            <span v-for="file in excelFiles" :key="file.name" class="pill">{{ file.name }}</span>
          </div>
          <p v-if="importMessage" class="muted status-message">{{ importMessage }}</p>
        </article>

        <article class="card admin-panel-block">
          <div class="title-row compact-row">
            <div>
              <strong>任务中心</strong>
              <p class="muted">企业后台常见的待处理事项收口区。</p>
            </div>
            <span class="pill">{{ operationsBoard.length }} 项</span>
          </div>
          <div class="grid" style="margin-top: 18px">
            <div v-for="task in operationsBoard" :key="task.title" class="timeline-item admin-task-card">
              <div class="title-row compact-row">
                <strong>{{ task.title }}</strong>
                <span class="pill">{{ task.value }}</span>
              </div>
              <p class="muted">{{ task.description }}</p>
            </div>
          </div>
        </article>
      </div>
    </article>

    <article v-if="currentTab === 'users'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="用户信息管理" description="左侧选择用户，右侧维护账号资料、头像、权限和启停状态。" />
        <button class="btn btn-secondary" type="button" @click="loadUsers">刷新用户</button>
      </div>

      <div class="field-grid" style="margin-top: 20px">
        <div class="field">
          <label>搜索用户</label>
          <input v-model.trim="userKeyword" placeholder="用户名、昵称、邮箱或常住城市" />
        </div>
        <div class="field">
          <label>按角色筛选</label>
          <select v-model="userRole">
            <option value="">全部角色</option>
            <option value="admin">管理员</option>
            <option value="member">普通用户</option>
          </select>
        </div>
        <div class="field">
          <label>按状态筛选</label>
          <select v-model="userStatus">
            <option value="">全部状态</option>
            <option value="active">启用中</option>
            <option value="disabled">已停用</option>
          </select>
        </div>
      </div>

      <div class="admin-grid admin-editor-grid" style="margin-top: 22px">
        <div class="admin-list admin-module-list">
          <button
            v-for="item in adminUsers"
            :key="item.id"
            class="timeline-item trip-button"
            :class="{ selected: selectedUser.id === item.id }"
            type="button"
            @click="pickUser(item)"
          >
            <div class="title-row compact-row">
              <strong>{{ item.nickname || item.username }}</strong>
              <span class="pill">{{ item.is_staff ? "Admin" : "User" }}</span>
            </div>
            <p class="muted">{{ item.username }} · {{ item.home_city || "未填写常住城市" }}</p>
          </button>
          <div v-if="!adminUsers.length" class="timeline-item">
            <strong>暂无匹配用户</strong>
            <p class="muted">可以调整筛选条件后再试一次。</p>
          </div>
        </div>

        <form class="grid admin-editor-form" @submit.prevent="handleSaveUser">
          <div class="field-grid">
            <div class="field">
              <label>用户名</label>
              <input v-model.trim="selectedUser.username" :disabled="!selectedUser.id" required />
            </div>
            <div class="field">
              <label>昵称</label>
              <input v-model.trim="selectedUser.nickname" :disabled="!selectedUser.id" />
            </div>
            <div class="field">
              <label>邮箱</label>
              <input v-model.trim="selectedUser.email" :disabled="!selectedUser.id" type="email" />
            </div>
            <div class="field">
              <label>常住城市</label>
              <input v-model.trim="selectedUser.home_city" :disabled="!selectedUser.id" />
            </div>
          </div>

          <div class="field">
            <label>头像上传</label>
            <FileUploadField
              v-model="selectedUser.avatar_url"
              category="avatar"
              accept=".png,.jpg,.jpeg,.webp,.gif"
              helper="后台可直接上传并维护用户头像文件。"
              preview-alt="user avatar preview"
            />
          </div>

          <div class="field">
            <label>个人简介</label>
            <textarea v-model.trim="selectedUser.bio" class="textarea" rows="4" :disabled="!selectedUser.id"></textarea>
          </div>

          <div class="field">
            <label>偏好风格</label>
            <input v-model.trim="userStylesInput" :disabled="!selectedUser.id" placeholder="多个风格用英文逗号分隔" />
          </div>

          <div class="grid grid-3 admin-user-summary-grid">
            <div class="mini-spot">
              <strong>{{ selectedUser.post_count || 0 }}</strong>
              <p class="muted">帖子数量</p>
            </div>
            <div class="mini-spot">
              <strong>{{ selectedUser.comment_count || 0 }}</strong>
              <p class="muted">评论数量</p>
            </div>
            <div class="mini-spot">
              <strong>{{ selectedUser.plan_count || 0 }}</strong>
              <p class="muted">AI 行程数量</p>
            </div>
          </div>

          <label class="checkbox-row">
            <input v-model="selectedUser.is_staff" :disabled="!selectedUser.id" type="checkbox" />
            <span>授予后台管理员权限</span>
          </label>
          <label class="checkbox-row">
            <input v-model="selectedUser.is_active" :disabled="!selectedUser.id" type="checkbox" />
            <span>账号保持启用状态</span>
          </label>

          <div class="action-row">
            <button class="btn btn-primary" type="submit" :disabled="!selectedUser.id">保存用户</button>
            <button class="btn btn-secondary" type="button" @click="handleDeleteUser" :disabled="!selectedUser.id">删除用户</button>
          </div>
        </form>
      </div>
    </article>

    <article v-if="currentTab === 'cities'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="城市资产中心" description="采用企业后台常见的“左侧列表 + 右侧编辑器”模式维护城市资产。" />
        <button class="btn btn-secondary" type="button" @click="resetCity">新建城市</button>
      </div>
      <div class="field" style="margin-top: 20px">
        <label for="cityKeyword">搜索城市</label>
        <input id="cityKeyword" v-model.trim="cityKeyword" placeholder="输入城市名、省份或简介" />
      </div>
      <div class="admin-grid admin-editor-grid" style="margin-top: 22px">
        <div class="admin-list admin-module-list">
          <button
            v-for="item in cities"
            :key="item.id"
            class="timeline-item trip-button"
            :class="{ selected: selectedCity.id === item.id }"
            type="button"
            @click="pickCity(item)"
          >
            <div class="title-row compact-row">
              <strong>{{ item.name }}</strong>
              <span class="pill">{{ item.attraction_count }} 景点</span>
            </div>
            <p class="muted">{{ item.province || "中国" }}</p>
          </button>
        </div>

        <form class="grid admin-editor-form" @submit.prevent="handleSaveCity">
          <div class="field-grid">
            <div class="field">
              <label>城市名称</label>
              <input v-model.trim="selectedCity.name" required />
            </div>
            <div class="field">
              <label>省份 / 直辖市</label>
              <input v-model.trim="selectedCity.province" />
            </div>
            <div class="field">
              <label>目的地类型</label>
              <select v-model="selectedCity.destination_type">
                <option value="city">城市</option>
                <option value="region">地区</option>
                <option value="scenic">景区</option>
              </select>
            </div>
            <div class="field">
              <label>推荐季节</label>
              <input v-model.trim="selectedCity.best_season" />
            </div>
          </div>

          <div class="field">
            <label>标签</label>
            <input v-model.trim="cityTagInput" placeholder="多个标签用英文逗号分隔" />
          </div>

          <div class="field">
            <label>封面上传</label>
            <FileUploadField
              v-model="selectedCity.cover_image"
              category="city-cover"
              accept=".png,.jpg,.jpeg,.webp,.gif"
              helper="城市封面图改为上传文件，不再手填图片 URL。"
              preview-alt="city cover preview"
            />
          </div>

          <div class="field">
            <label>短介绍</label>
            <textarea v-model.trim="selectedCity.short_intro" class="textarea" rows="3"></textarea>
          </div>
          <div class="field">
            <label>概览</label>
            <textarea v-model.trim="selectedCity.overview" class="textarea" rows="6"></textarea>
          </div>
          <div class="field">
            <label>玩法亮点</label>
            <textarea v-model.trim="selectedCity.travel_highlights" class="textarea" rows="4"></textarea>
          </div>
          <div class="field">
            <label>出行建议</label>
            <textarea v-model.trim="selectedCity.travel_tips" class="textarea" rows="4"></textarea>
          </div>
          <label class="checkbox-row">
            <input v-model="selectedCity.is_featured" type="checkbox" />
            <span>设为首页推荐城市</span>
          </label>
          <div class="action-row">
            <button class="btn btn-primary" type="submit">保存城市</button>
            <button class="btn btn-secondary" type="button" @click="handleDeleteCity" :disabled="!selectedCity.id">删除城市</button>
          </div>
        </form>
      </div>
    </article>

    <article v-if="currentTab === 'attractions'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="景点资产中心" description="用更规整的后台编辑器维护景点图片、来源链接和结构化信息。" />
        <button class="btn btn-secondary" type="button" @click="resetAttraction">新建景点</button>
      </div>
      <div class="field-grid" style="margin-top: 20px">
        <div class="field">
          <label>搜索景点</label>
          <input v-model.trim="attractionKeyword" placeholder="景点名、地址、介绍" />
        </div>
        <div class="field">
          <label>按城市筛选</label>
          <select v-model="attractionCityId">
            <option value="">全部城市</option>
            <option v-for="city in cityOptions" :key="city.id" :value="String(city.id)">{{ city.name }}</option>
          </select>
        </div>
      </div>

      <div class="admin-grid admin-editor-grid" style="margin-top: 22px">
        <div class="admin-list admin-module-list">
          <button
            v-for="item in attractions"
            :key="item.id"
            class="timeline-item trip-button"
            :class="{ selected: selectedAttraction.id === item.id }"
            type="button"
            @click="pickAttraction(item)"
          >
            <div class="title-row compact-row">
              <strong>{{ item.name }}</strong>
              <span class="pill">{{ item.rating || "--" }}</span>
            </div>
            <p class="muted">{{ item.city_name }}</p>
          </button>
        </div>

        <form class="grid admin-editor-form" @submit.prevent="handleSaveAttraction">
          <div class="field-grid">
            <div class="field">
              <label>所属城市</label>
              <select v-model="selectedAttraction.city" required>
                <option value="" disabled>请选择城市</option>
                <option v-for="city in cityOptions" :key="city.id" :value="city.id">{{ city.name }}</option>
              </select>
            </div>
            <div class="field">
              <label>景点名称</label>
              <input v-model.trim="selectedAttraction.name" required />
            </div>
            <div class="field">
              <label>评分</label>
              <input v-model="selectedAttraction.rating" type="number" min="0" max="5" step="0.1" />
            </div>
            <div class="field">
              <label>建议游玩时间</label>
              <input v-model.trim="selectedAttraction.suggested_play_time" />
            </div>
          </div>

          <div class="field">
            <label>景点图片上传</label>
            <FileUploadField
              v-model="selectedAttraction.image_url"
              category="attraction-image"
              accept=".png,.jpg,.jpeg,.webp,.gif"
              helper="上传景点图片后会自动回填访问地址。"
              preview-alt="attraction preview"
            />
          </div>
          <div class="field">
            <label>来源链接</label>
            <input v-model.trim="selectedAttraction.source_url" placeholder="可选，保留外部资料页面链接" />
          </div>
          <div class="field">
            <label>地址</label>
            <textarea v-model.trim="selectedAttraction.address" class="textarea" rows="3"></textarea>
          </div>
          <div class="field">
            <label>开放时间</label>
            <textarea v-model.trim="selectedAttraction.opening_hours" class="textarea" rows="3"></textarea>
          </div>
          <div class="field">
            <label>门票信息</label>
            <textarea v-model.trim="selectedAttraction.ticket_info" class="textarea" rows="3"></textarea>
          </div>
          <div class="field">
            <label>景点介绍</label>
            <textarea v-model.trim="selectedAttraction.description" class="textarea" rows="6"></textarea>
          </div>
          <div class="field">
            <label>标签</label>
            <input v-model.trim="attractionTagInput" placeholder="多个标签用英文逗号分隔" />
          </div>
          <div class="action-row">
            <button class="btn btn-primary" type="submit">保存景点</button>
            <button class="btn btn-secondary" type="button" @click="handleDeleteAttraction" :disabled="!selectedAttraction.id">删除景点</button>
          </div>
        </form>
      </div>
    </article>

    <article v-if="currentTab === 'posts'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="社区内容审核台" description="将帖子管理整理成更接近企业后台审核台的列表视图。" />
        <span class="pill">{{ adminPosts.length }} 条</span>
      </div>
      <div class="field-grid" style="margin-top: 20px">
        <div class="field">
          <label>搜索帖子</label>
          <input v-model.trim="postKeyword" placeholder="标题或正文关键词" />
        </div>
        <div class="field">
          <label>按城市筛选</label>
          <select v-model="postCityId">
            <option value="">全部城市</option>
            <option v-for="city in cityOptions" :key="city.id" :value="String(city.id)">{{ city.name }}</option>
          </select>
        </div>
      </div>
      <div class="grid" style="margin-top: 24px">
        <div v-for="post in adminPosts" :key="post.id" class="timeline-item admin-post-card">
          <div class="title-row">
            <div>
              <strong>{{ post.title }}</strong>
              <p class="muted">{{ post.author_name }} · {{ post.city_name || "未关联城市" }} · {{ post.attraction_name || "未关联景点" }}</p>
            </div>
            <button class="btn btn-secondary" type="button" @click="handleDeletePost(post.id)">删除</button>
          </div>
          <p class="muted clamp-4">{{ post.content }}</p>
        </div>
      </div>
    </article>

    <article v-if="currentTab === 'logs'" class="card section-shell">
      <div class="title-row">
        <SectionHeader title="系统操作日志" description="采用更接近企业后台的审计表格，方便按分类和状态快速回溯。" />
        <span class="pill">{{ adminLogs.length }} 条</span>
      </div>
      <div class="field-grid" style="margin-top: 20px">
        <div class="field">
          <label>按分类筛选</label>
          <select v-model="logCategory">
            <option value="">全部分类</option>
            <option v-for="category in logCategories" :key="category" :value="category">{{ category }}</option>
          </select>
        </div>
        <div class="field">
          <label>按状态筛选</label>
          <select v-model="logStatus">
            <option value="">全部状态</option>
            <option value="success">success</option>
            <option value="failed">failed</option>
          </select>
        </div>
      </div>

      <div class="table-wrap" style="margin-top: 24px">
        <table class="table admin-log-table">
          <thead>
            <tr>
              <th>操作</th>
              <th>分类</th>
              <th>操作者</th>
              <th>目标</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in adminLogs" :key="log.id">
              <td>{{ log.action }}</td>
              <td>{{ log.category }}</td>
              <td>{{ log.nickname || log.username || "匿名" }}</td>
              <td>{{ log.target_name || log.request_path }}</td>
              <td>{{ log.status }}</td>
              <td>{{ formatDateTime(log.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import DashboardBarChart from "../components/backoffice/DashboardBarChart.vue";
import DashboardDonutChart from "../components/backoffice/DashboardDonutChart.vue";
import FileUploadField from "../components/FileUploadField.vue";
import SectionHeader from "../components/SectionHeader.vue";
import {
  deleteAdminAttraction,
  deleteAdminCity,
  deleteAdminPost,
  deleteAdminUser,
  getAdminAttractions,
  getAdminCities,
  getAdminLogs,
  getAdminPosts,
  getAdminSummary,
  getAdminUsers,
  importExcelFiles,
  saveAdminAttraction,
  saveAdminCity,
  saveAdminUser,
} from "../services/api";


const route = useRoute();
const router = useRouter();

const currentTab = ref(route.query.tab || "overview");
const summary = ref({ user_count: 0, city_count: 0, attraction_count: 0, post_count: 0, comment_count: 0, top_cities: [], recent_logs: [] });
const cityOptions = ref([]);
const cities = ref([]);
const attractions = ref([]);
const adminUsers = ref([]);
const adminPosts = ref([]);
const adminLogs = ref([]);
const adminMessage = ref("");
const importMessage = ref("");

const userKeyword = ref("");
const userRole = ref("");
const userStatus = ref("");
const userStylesInput = ref("");
const selectedUser = ref(createEmptyUser());

const cityKeyword = ref("");
const cityTagInput = ref("");
const selectedCity = ref(createEmptyCity());

const attractionKeyword = ref("");
const attractionCityId = ref("");
const attractionTagInput = ref("");
const selectedAttraction = ref(createEmptyAttraction());

const postKeyword = ref("");
const postCityId = ref("");

const logCategory = ref("");
const logStatus = ref("");

const excelFiles = ref([]);
const importForm = ref({
  overwrite: false,
});

const topCityChartItems = computed(() =>
  (summary.value.top_cities || []).slice(0, 6).map((city) => ({
    label: city.name,
    value: city.attraction_count || 0,
  })),
);

const contentComposition = computed(() => [
  { label: "城市", value: summary.value.city_count || 0 },
  { label: "景点", value: summary.value.attraction_count || 0 },
  { label: "帖子", value: summary.value.post_count || 0 },
  { label: "评论", value: summary.value.comment_count || 0 },
]);

const kpiCards = computed(() => [
  { label: "用户数", value: summary.value.user_count || 0, caption: "账号资产" },
  { label: "城市数", value: summary.value.city_count || 0, caption: "地图资产" },
  { label: "景点数", value: summary.value.attraction_count || 0, caption: "可直接钻取" },
  { label: "帖子数", value: summary.value.post_count || 0, caption: "社区内容" },
  { label: "评论数", value: summary.value.comment_count || 0, caption: "互动总量" },
]);

const recentLogs = computed(() => (summary.value.recent_logs || []).slice(0, 5));
const logCategories = computed(() => [...new Set(adminLogs.value.map((item) => item.category))]);

const systemSignals = computed(() => [
  {
    label: "用户账户",
    state: summary.value.user_count > 0 ? "Ready" : "Empty",
    description: `当前共维护 ${summary.value.user_count || 0} 个用户账号，可在用户管理模块统一维护。`,
  },
  {
    label: "媒体上传",
    state: "Online",
    description: "图片与文件上传链路可用，支持头像、封面、景点图和 Excel 入库。",
  },
  {
    label: "内容审计",
    state: recentLogs.value.length ? "Tracking" : "Idle",
    description: `最近已记录 ${recentLogs.value.length} 条关键后台操作日志。`,
  },
  {
    label: "城市资产",
    state: summary.value.city_count > 0 ? "Ready" : "Empty",
    description: `当前共维护 ${summary.value.city_count || 0} 个城市数据节点。`,
  },
]);

const operationsBoard = computed(() => [
  {
    title: "用户资料治理",
    value: summary.value.user_count || 0,
    description: "用户账号、头像和资料已纳入后台统一管理。",
  },
  {
    title: "高优先级内容资产",
    value: topCityChartItems.value[0]?.label || "暂无",
    description: topCityChartItems.value[0] ? `当前景点覆盖最高的城市为 ${topCityChartItems.value[0].label}。` : "等待导入城市与景点数据。",
  },
  {
    title: "日志采集",
    value: summary.value.recent_logs?.length || 0,
    description: "后台关键操作已接入日志采集，可用于审计和问题回溯。",
  },
]);

function createEmptyUser() {
  return {
    id: null,
    username: "",
    email: "",
    nickname: "",
    avatar_url: "",
    bio: "",
    home_city: "",
    favorite_styles: [],
    is_staff: false,
    is_active: true,
    is_superuser: false,
    date_joined: "",
    last_login: "",
    post_count: 0,
    comment_count: 0,
    plan_count: 0,
  };
}

function createEmptyCity() {
  return {
    id: null,
    name: "",
    province: "",
    destination_type: "city",
    short_intro: "",
    overview: "",
    travel_highlights: "",
    cover_image: "",
    best_season: "",
    recommended_days: 3,
    average_ticket: "",
    tags: [],
    travel_tips: "",
    is_featured: false,
  };
}

function createEmptyAttraction(cityId = "") {
  return {
    id: null,
    city: cityId || "",
    name: "",
    source_url: "",
    address: "",
    description: "",
    opening_hours: "",
    image_url: "",
    rating: "",
    suggested_play_time: "",
    best_season: "",
    ticket_info: "",
    tips: "",
    source_page: 1,
    tags: [],
  };
}

function parseCommaList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function switchTab(tab) {
  currentTab.value = tab;
  router.replace({ name: "backoffice", query: { tab } });
}

function pickUser(item) {
  selectedUser.value = { ...createEmptyUser(), ...item };
  userStylesInput.value = (selectedUser.value.favorite_styles || []).join(", ");
}

function resetUser() {
  pickUser(createEmptyUser());
}

function pickCity(item) {
  selectedCity.value = { ...createEmptyCity(), ...item };
  cityTagInput.value = (selectedCity.value.tags || []).join(", ");
}

function resetCity() {
  pickCity(createEmptyCity());
}

function pickAttraction(item) {
  selectedAttraction.value = { ...createEmptyAttraction(attractionCityId.value), ...item };
  attractionTagInput.value = (selectedAttraction.value.tags || []).join(", ");
}

function resetAttraction() {
  pickAttraction(createEmptyAttraction(attractionCityId.value || selectedCity.value.id));
}

function resolveError(error) {
  const detail = error?.response?.data?.detail;
  if (detail) return detail;
  return "操作失败，请检查输入内容。";
}

function handleExcelChange(event) {
  excelFiles.value = [...(event.target.files || [])];
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "";
}

async function loadSummary() {
  summary.value = await getAdminSummary();
}

async function loadCityOptions() {
  cityOptions.value = await getAdminCities({ limit: 500 });
}

async function loadUsers() {
  const activeId = selectedUser.value.id;
  adminUsers.value = await getAdminUsers({
    q: userKeyword.value || undefined,
    role: userRole.value || undefined,
    status: userStatus.value || undefined,
    limit: 120,
  });
  const next = adminUsers.value.find((item) => item.id === activeId) || adminUsers.value[0];
  if (next) {
    pickUser(next);
  } else {
    resetUser();
  }
}

async function loadCities() {
  const activeId = selectedCity.value.id;
  cities.value = await getAdminCities({ q: cityKeyword.value || undefined, limit: 100 });
  const next = cities.value.find((item) => item.id === activeId) || cities.value[0];
  if (next) {
    pickCity(next);
  } else {
    resetCity();
  }
}

async function loadAttractions() {
  const activeId = selectedAttraction.value.id;
  attractions.value = await getAdminAttractions({
    q: attractionKeyword.value || undefined,
    city_id: attractionCityId.value || undefined,
    limit: 120,
  });
  const next = attractions.value.find((item) => item.id === activeId) || attractions.value[0];
  if (next) {
    pickAttraction(next);
  } else {
    resetAttraction();
  }
}

async function loadPosts() {
  adminPosts.value = await getAdminPosts({
    q: postKeyword.value || undefined,
    city_id: postCityId.value || undefined,
    limit: 80,
  });
}

async function loadLogs() {
  adminLogs.value = await getAdminLogs({
    category: logCategory.value || undefined,
    status: logStatus.value || undefined,
    limit: 120,
  });
}

async function refreshAll() {
  await Promise.all([loadSummary(), loadCityOptions(), loadUsers(), loadCities(), loadAttractions(), loadPosts(), loadLogs()]);
}

async function handleImportFiles() {
  if (!excelFiles.value.length) return;
  try {
    const result = await importExcelFiles(excelFiles.value, importForm.value.overwrite);
    importMessage.value = result.detail;
    adminMessage.value = "Excel 文件导入完成。";
    excelFiles.value = [];
    await refreshAll();
  } catch (error) {
    importMessage.value = resolveError(error);
  }
}

async function handleSaveUser() {
  if (!selectedUser.value.id) return;
  try {
    const saved = await saveAdminUser({
      ...selectedUser.value,
      favorite_styles: parseCommaList(userStylesInput.value),
    });
    adminMessage.value = "用户信息已更新。";
    await Promise.all([loadSummary(), loadUsers(), loadLogs()]);
    pickUser(saved);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleDeleteUser() {
  if (!selectedUser.value.id) return;
  try {
    await deleteAdminUser(selectedUser.value.id);
    adminMessage.value = "用户已删除。";
    await Promise.all([loadSummary(), loadUsers(), loadLogs()]);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleSaveCity() {
  try {
    const saved = await saveAdminCity({ ...selectedCity.value, tags: parseCommaList(cityTagInput.value) });
    adminMessage.value = selectedCity.value.id ? "城市信息已更新。" : "已创建新的城市记录。";
    await Promise.all([loadSummary(), loadCityOptions(), loadCities(), loadLogs()]);
    pickCity(saved);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleDeleteCity() {
  if (!selectedCity.value.id) return;
  try {
    await deleteAdminCity(selectedCity.value.id);
    adminMessage.value = "城市已删除。";
    await Promise.all([loadSummary(), loadCityOptions(), loadCities(), loadAttractions(), loadLogs()]);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleSaveAttraction() {
  try {
    const saved = await saveAdminAttraction({
      ...selectedAttraction.value,
      city: selectedAttraction.value.city ? Number(selectedAttraction.value.city) : "",
      source_page: Number(selectedAttraction.value.source_page || 1),
      rating: selectedAttraction.value.rating === "" ? null : selectedAttraction.value.rating,
      tags: parseCommaList(attractionTagInput.value),
    });
    adminMessage.value = selectedAttraction.value.id ? "景点信息已更新。" : "已创建新的景点记录。";
    await Promise.all([loadSummary(), loadCities(), loadAttractions(), loadLogs()]);
    pickAttraction(saved);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleDeleteAttraction() {
  if (!selectedAttraction.value.id) return;
  try {
    await deleteAdminAttraction(selectedAttraction.value.id);
    adminMessage.value = "景点已删除。";
    await Promise.all([loadSummary(), loadCities(), loadAttractions(), loadLogs()]);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

async function handleDeletePost(id) {
  try {
    await deleteAdminPost(id);
    adminMessage.value = "帖子已删除。";
    await Promise.all([loadSummary(), loadPosts(), loadLogs()]);
  } catch (error) {
    adminMessage.value = resolveError(error);
  }
}

watch([userKeyword, userRole, userStatus], loadUsers);
watch(cityKeyword, loadCities);
watch([attractionKeyword, attractionCityId], loadAttractions);
watch([postKeyword, postCityId], loadPosts);
watch([logCategory, logStatus], loadLogs);
watch(
  () => route.query.tab,
  (value) => {
    currentTab.value = value || "overview";
  },
);

onMounted(refreshAll);
</script>
