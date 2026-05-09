<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-kicker">Smart Ranch OS</p>
        <h1>智慧养殖云平台</h1>
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
        <div class="topbar-copy">
          <p class="topbar-kicker">{{ currentRoute.label }}</p>
          <h2>{{ currentRoute.headline }}</h2>
        </div>
        <div v-if="currentRoute.key === 'home'" class="topbar-summary-strip">
          <article v-for="card in topbarSummaryCards" :key="card.title" class="topbar-summary-chip">
            <span>{{ card.title }}</span>
            <strong>{{ card.value }}</strong>
            <small>{{ card.subtitle }}</small>
          </article>
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

      <div class="notice-stack" :class="{ 'notice-stack--home': currentRoute.key === 'home' }">
        <transition name="notice-fade">
          <section v-if="activeError" class="global-notice error">
            <strong>页面提醒</strong>
            <span>{{ activeError }}</span>
          </section>
        </transition>

        <transition name="notice-fade">
          <section v-if="monitoringStore.notice.visible" class="global-notice" :class="monitoringStore.notice.type">
            <strong v-if="monitoringStore.notice.title">{{ monitoringStore.notice.title }}</strong>
            <span>{{ monitoringStore.notice.message }}</span>
          </section>
        </transition>
      </div>

      <main class="page-body" :class="`page-${currentRoute.key}`">
        <component :is="currentRoute.component" :navigate="navigate" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, markRaw, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useMonitoringStore } from './stores/monitoring'

const OverviewHome = defineAsyncComponent(() => import('./views/OverviewHome.vue'))
const MonitoringView = defineAsyncComponent(() => import('./views/MonitoringView.vue'))
const ControlView = defineAsyncComponent(() => import('./views/ControlView.vue'))
const ArchivesView = defineAsyncComponent(() => import('./views/ArchivesView.vue'))
const AlarmsView = defineAsyncComponent(() => import('./views/AlarmsView.vue'))
const OperationsView = defineAsyncComponent(() => import('./views/OperationsView.vue'))
const SystemView = defineAsyncComponent(() => import('./views/SystemView.vue'))

const monitoringStore = useMonitoringStore()
const currentPath = ref(window.location.pathname || '/')
const currentTime = ref(new Date().toLocaleString('zh-CN'))
const isPageVisible = ref(typeof document === 'undefined' ? true : document.visibilityState === 'visible')
let clockTimer = null
let refreshTimer = null

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
const activeError = computed(() => {
  const message = monitoringStore.errorByModule[currentRoute.value.key] || ''
  if (!message) return ''
  if (message.includes('timeout of 10000ms exceeded')) return ''
  return message
})
const topbarSummaryCards = computed(() => [
  {
    title: '监测区域',
    value: monitoringStore.overview.summary.zone_count || 0,
    subtitle: `${monitoringStore.overview.summary.device_count || 0} 台设备`
  },
  {
    title: '待处理告警',
    value: monitoringStore.alarms.length,
    subtitle: `高风险 ${monitoringStore.riskDashboard.summary.highest_risk_zone || '--'}`
  },
  {
    title: '今日任务',
    value: monitoringStore.operationsDashboard.summary.pending_tasks || 0,
    subtitle: `库存预警 ${monitoringStore.operationsDashboard.summary.low_stock_items || 0}`
  },
  {
    title: '活跃用户',
    value: monitoringStore.systemDashboard.summary.active_users || 0,
    subtitle: `批次 ${monitoringStore.archiveDashboard.summary.active_batches || 0}`
  }
])

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
  clockTimer = window.setInterval(() => {
    currentTime.value = new Date().toLocaleString('zh-CN')
  }, 1000)
  refreshTimer = window.setInterval(() => {
    if (!isPageVisible.value || monitoringStore.loading) return
    monitoringStore.loadModule(currentRoute.value.key, { silent: true })
  }, 5000)
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
  if (clockTimer) window.clearInterval(clockTimer)
  if (refreshTimer) window.clearInterval(refreshTimer)
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
  font-size: 17px;
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
  font-size: 13px;
}

.brand h1,
.topbar h2 {
  margin: 0;
  line-height: 1.2;
}

.brand h1 {
  font-size: 36px;
}

.topbar h2 {
  font-size: 32px;
}

.brand-text {
  margin: 12px 0 0;
  color: var(--text-muted);
  line-height: 1.7;
  font-size: 17px;
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
  font-size: 18px;
}

.nav-copy small {
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.5;
}

.status-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 24px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--border-soft);
  background: rgba(10, 33, 39, 0.84);
  color: var(--text-main);
}

.status-banner strong {
  font-size: 16px;
}

.status-banner span {
  color: var(--text-muted);
  font-size: 15px;
}

.status-banner.info {
  border-color: rgba(95, 194, 170, 0.22);
  background: rgba(95, 194, 170, 0.08);
}

.status-banner.error {
  border-color: rgba(255, 133, 127, 0.24);
  background: rgba(255, 133, 127, 0.08);
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
  font-size: 15px;
  margin-bottom: 8px;
}

.sidebar-foot strong {
  font-size: 19px;
}

.workspace {
  padding: 24px;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.topbar-copy {
  min-width: 0;
}

.topbar-summary-strip {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.topbar-summary-chip {
  min-width: 0;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(12, 36, 42, 0.7);
  border: 1px solid var(--border-soft);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topbar-summary-chip span {
  color: var(--text-muted);
  font-size: 12px;
}

.topbar-summary-chip strong {
  font-size: 20px;
  line-height: 1.1;
}

.topbar-summary-chip small {
  color: #bfd3d3;
  font-size: 12px;
  line-height: 1.35;
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
  font-size: 14px;
  margin-bottom: 6px;
}

.meta-chip strong {
  font-size: 18px;
}

.status-banner {
  margin-bottom: 18px;
  padding: 14px 18px;
  border-radius: 18px;
  border: 1px solid var(--border-soft);
  font-size: 16px;
  line-height: 1.6;
}

.status-banner.error {
  background: rgba(64, 24, 24, 0.9);
  border-color: rgba(255, 133, 127, 0.3);
  color: #ffd6d2;
}

.page-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.page-body.page-monitoring,
.page-body.page-archives,
.page-body.page-alarms,
.page-body.page-operations,
.page-body.page-system {
  overflow: hidden;
}

.notice-stack {
  position: fixed;
  top: 26px;
  left: calc(280px + (100vw - 280px) / 2);
  transform: translateX(-50%);
  z-index: 1200;
  display: grid;
  gap: 10px;
  justify-items: center;
  pointer-events: none;
}

.notice-stack--home {
  top: auto;
  right: 22px;
  bottom: 22px;
  left: auto;
  transform: none;
  justify-items: end;
}

.global-notice {
  width: min(340px, calc(100vw - 32px));
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(176, 224, 221, 0.16);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(14px);
  pointer-events: auto;
}

.global-notice strong {
  font-size: 14px;
  color: #f5fbfc;
}

.global-notice span {
  font-size: 13px;
  line-height: 1.45;
}

.global-notice.info {
  background: rgba(12, 41, 47, 0.9);
  color: #d6ebef;
}

.global-notice.success {
  background: rgba(18, 61, 54, 0.92);
  border-color: rgba(95, 211, 188, 0.24);
  color: #d5f4ec;
}

.global-notice.error {
  background: rgba(64, 26, 30, 0.9);
  border-color: rgba(255, 133, 127, 0.24);
  color: #ffd8d5;
}

.notice-fade-enter-active,
.notice-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.notice-fade-enter-from,
.notice-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
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
  font-size: 28px;
}

.section-heading p {
  margin: 0 0 6px;
  color: var(--text-muted);
  font-size: 16px;
  line-height: 1.6;
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
  font-size: 15px;
  color: var(--text-muted);
}

.toolbar-field select,
.toolbar-field input {
  height: 44px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid var(--border-strong);
  background: rgba(7, 26, 31, 0.94);
  color: var(--text-main);
  font-size: 16px;
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

  .topbar-summary-strip,
  .topbar-meta {
    width: 100%;
  }

  .topbar-summary-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .meta-chip {
    flex: 1;
  }
}

@media (max-width: 760px) {
  .topbar-summary-strip {
    grid-template-columns: 1fr;
  }

  .notice-stack {
    top: 88px;
    left: 50%;
    transform: translateX(-50%);
  }

  .notice-stack--home {
    right: 12px;
    bottom: 12px;
    left: auto;
    top: auto;
    transform: none;
  }
}
</style>
