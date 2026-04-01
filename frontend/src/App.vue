<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-kicker">Smart Ranch OS</p>
        <h1>智慧养殖协同平台</h1>
        <p class="brand-text">把监测、控制、档案、预警、任务和权限拆成清晰模块，操作更聚焦。</p>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in navigationItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
          @click="navigate(item.path)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-copy">
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
          </span>
        </button>
      </nav>

      <div class="sidebar-foot">
        <span>运行状态</span>
        <strong>{{ monitoringStore.loading ? '正在同步数据' : '系统在线' }}</strong>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div>
          <p class="topbar-kicker">{{ currentRoute.label }}</p>
          <h2>{{ currentRoute.headline }}</h2>
        </div>
        <div class="topbar-meta">
          <div class="meta-chip">
            <span>当前时间</span>
            <strong>{{ currentTime }}</strong>
          </div>
          <div class="meta-chip">
            <span>活跃区域</span>
            <strong>{{ monitoringStore.selectedZone || '未选择' }}</strong>
          </div>
        </div>
      </header>

      <section v-if="activeError" class="status-banner error">
        {{ activeError }}
      </section>

      <main class="page-body">
        <component :is="currentRoute.component" :navigate="navigate" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, markRaw, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import OverviewHome from './views/OverviewHome.vue'
import MonitoringView from './views/MonitoringView.vue'
import ControlView from './views/ControlView.vue'
import ArchivesView from './views/ArchivesView.vue'
import AlarmsView from './views/AlarmsView.vue'
import OperationsView from './views/OperationsView.vue'
import SystemView from './views/SystemView.vue'
import { useMonitoringStore } from './stores/monitoring'

const monitoringStore = useMonitoringStore()
const currentPath = ref(window.location.pathname || '/')
const currentTime = ref(new Date().toLocaleString('zh-CN'))
const isPageVisible = ref(typeof document === 'undefined' ? true : document.visibilityState === 'visible')
let timer = null

const routes = [
  { path: '/', key: 'home', label: '总览首页', headline: '全局概览与快捷入口', icon: '总', description: '先看全局状态', component: markRaw(OverviewHome) },
  { path: '/monitoring', key: 'monitoring', label: '环境监测', headline: '实时感知与历史趋势分析', icon: '监', description: '温湿度与气体数据', component: markRaw(MonitoringView) },
  { path: '/control', key: 'control', label: '智能控制', headline: '设备联动与控制留痕', icon: '控', description: '风机水帘补光灯', component: markRaw(ControlView) },
  { path: '/archives', key: 'archives', label: '养殖档案', headline: '批次档案与牛羊个体档案', icon: '档', description: '批次与个体信息', component: markRaw(ArchivesView) },
  { path: '/alarms', key: 'alarms', label: '风险预警', headline: '待处理告警与风险摘要', icon: '警', description: '告警与风险分布', component: markRaw(AlarmsView) },
  { path: '/operations', key: 'operations', label: '任务资产', headline: '生产任务、库存与设备资产', icon: '务', description: '任务与资产管理', component: markRaw(OperationsView) },
  { path: '/system', key: 'system', label: '系统权限', headline: '用户、角色与操作日志', icon: '权', description: '系统管理中心', component: markRaw(SystemView) }
]

const routeMap = Object.fromEntries(routes.map(route => [route.path, route]))
const currentRoute = computed(() => routeMap[currentPath.value] || routeMap['/'])
const navigationItems = routes
const activeError = computed(() => monitoringStore.errorByModule[currentRoute.value.key] || '')

function navigate(path) {
  if (path === currentPath.value) return
  window.history.pushState({}, '', path)
  currentPath.value = path
}

function handlePopState() {
  currentPath.value = window.location.pathname || '/'
}

function handleVisibilityChange() {
  isPageVisible.value = document.visibilityState === 'visible'
  if (isPageVisible.value) {
    monitoringStore.loadModule(currentRoute.value.key, { silent: true })
  }
}

async function loadRouteData(routeKey) {
  await monitoringStore.loadModule(routeKey)
}

onMounted(async () => {
  window.addEventListener('popstate', handlePopState)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  await loadRouteData(currentRoute.value.key)
  timer = window.setInterval(() => {
    currentTime.value = new Date().toLocaleString('zh-CN')
    if (!isPageVisible.value || monitoringStore.loading) return
    monitoringStore.loadModule(currentRoute.value.key, { silent: true })
  }, 15000)
})

watch(
  () => currentRoute.value.key,
  async (routeKey) => {
    await loadRouteData(routeKey)
  }
)

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handlePopState)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (timer) window.clearInterval(timer)
})
</script>

<style lang="scss">
:root {
  color-scheme: dark;
  --bg-app: #071419;
  --bg-panel: rgba(10, 33, 39, 0.88);
  --bg-panel-soft: rgba(14, 44, 52, 0.76);
  --bg-panel-strong: rgba(17, 53, 62, 0.94);
  --border-soft: rgba(176, 224, 221, 0.12);
  --border-strong: rgba(176, 224, 221, 0.22);
  --text-main: #eef7f7;
  --text-muted: #8faab0;
  --accent: #5ec2aa;
  --accent-warm: #f3bb55;
  --danger: #ff857f;
  --shadow-soft: 0 20px 50px rgba(0, 0, 0, 0.24);
}

html,
body,
#app {
  margin: 0;
  width: 100%;
  min-height: 100vh;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg-app);
  color: var(--text-main);
}

body {
  background:
    radial-gradient(circle at top left, rgba(94, 194, 170, 0.16), transparent 24%),
    radial-gradient(circle at right center, rgba(243, 187, 85, 0.1), transparent 22%),
    linear-gradient(160deg, #071419 0%, #0d2228 50%, #08181d 100%);
}

* {
  box-sizing: border-box;
}

button,
select,
input {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px 20px;
  border-right: 1px solid var(--border-soft);
  background: linear-gradient(180deg, rgba(7, 20, 25, 0.98), rgba(8, 24, 29, 0.92));
}

.brand {
  padding: 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(16, 46, 53, 0.96), rgba(10, 31, 37, 0.96));
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-soft);
}

.brand-kicker,
.topbar-kicker {
  margin: 0 0 8px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-size: 12px;
}

.brand h1,
.topbar h2 {
  margin: 0;
}

.brand-text {
  margin: 12px 0 0;
  color: var(--text-muted);
  line-height: 1.7;
  font-size: 14px;
}

.nav-list {
  display: grid;
  gap: 10px;
}

.nav-item {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-main);
  cursor: pointer;
  text-align: left;
  transition: 0.2s ease;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(20, 58, 67, 0.76);
  border-color: var(--border-strong);
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(94, 194, 170, 0.12);
  color: #d8faf0;
  font-weight: 700;
}

.nav-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-copy strong {
  font-size: 15px;
}

.nav-copy small {
  color: var(--text-muted);
}

.sidebar-foot {
  margin-top: auto;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(13, 37, 43, 0.88);
  border: 1px solid var(--border-soft);
}

.sidebar-foot span {
  display: block;
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 8px;
}

.workspace {
  padding: 24px;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.topbar-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-chip {
  min-width: 160px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(12, 36, 42, 0.84);
  border: 1px solid var(--border-soft);
}

.meta-chip span {
  display: block;
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.status-banner {
  margin-bottom: 18px;
  padding: 14px 18px;
  border-radius: 18px;
  border: 1px solid var(--border-soft);
}

.status-banner.error {
  background: rgba(64, 24, 24, 0.9);
  border-color: rgba(255, 133, 127, 0.3);
  color: #ffd6d2;
}

.page-body {
  min-height: calc(100vh - 160px);
}

.page-grid {
  display: grid;
  gap: 18px;
}

.page-panel {
  padding: 22px;
  border-radius: 24px;
  background: var(--bg-panel);
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-soft);
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.section-heading h3 {
  margin: 0;
  font-size: 24px;
}

.section-heading p {
  margin: 0 0 6px;
  color: var(--text-muted);
}

.toolbar-card {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 18px;
  border-radius: 22px;
  background: var(--bg-panel-soft);
  border: 1px solid var(--border-soft);
}

.toolbar-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 180px;
  flex: 1;
}

.toolbar-field label {
  font-size: 13px;
  color: var(--text-muted);
}

.toolbar-field select,
.toolbar-field input {
  height: 42px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid var(--border-strong);
  background: rgba(7, 26, 31, 0.94);
  color: var(--text-main);
}

@media (max-width: 1180px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid var(--border-soft);
  }
}

@media (max-width: 900px) {
  .workspace,
  .sidebar {
    padding: 16px;
  }

  .topbar {
    flex-direction: column;
  }

  .topbar-meta {
    width: 100%;
  }

  .meta-chip {
    flex: 1;
  }
}
</style>
