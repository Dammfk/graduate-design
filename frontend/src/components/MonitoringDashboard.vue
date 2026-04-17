<template>
  <div class="monitoring-page">
    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">模块一到模块六</p>
        <h1>环境监测、设备控制、养殖档案、风险预警、生产管理与系统权限协同看板</h1>
        <p class="hero-text">
          当前版本已经把六个核心模块串联起来，支持实时监测、远程控制、档案追踪、风险预警、生产任务资产管理和系统权限管理联动查看。
        </p>
      </div>

      <div class="hero-summary">
        <article class="summary-card">
          <span>监测区域</span>
          <strong>{{ monitoringStore.overview.summary.zone_count }}</strong>
        </article>
        <article class="summary-card">
          <span>在线设备</span>
          <strong>{{ monitoringStore.overview.summary.online_count }}</strong>
        </article>
        <article class="summary-card">
          <span>待处理任务</span>
          <strong>{{ monitoringStore.operationsDashboard.summary.pending_tasks ?? 0 }}</strong>
        </article>
        <article class="summary-card">
          <span>活跃用户</span>
          <strong>{{ monitoringStore.systemDashboard.summary.active_users ?? 0 }}</strong>
        </article>
      </div>
    </header>

    <section v-if="monitoringStore.lastRefreshError" class="status-banner error">
      {{ monitoringStore.lastRefreshError }}
    </section>

    <section class="toolbar">
      <div class="field-group">
        <label>监测区域</label>
        <select v-model="monitoringStore.selectedZone" @change="handleZoneChange">
          <option v-for="zone in monitoringStore.zoneOptions" :key="zone.zone_name" :value="zone.zone_name">
            {{ zone.zone_name }}（{{ zone.device_count }} 台设备）
          </option>
        </select>
      </div>
      <div class="field-group">
        <label>监测设备</label>
        <select v-model="monitoringStore.selectedDeviceId" @change="handleDeviceChange">
          <option v-for="device in monitoringStore.currentZoneDevices" :key="device.device_id" :value="device.device_id">
            {{ device.device_name }} / {{ device.device_id }}
          </option>
        </select>
      </div>
      <div class="field-group compact">
        <label>趋势时长</label>
        <select v-model.number="monitoringStore.selectedHours" @change="handleDeviceChange">
          <option :value="6">近 6 小时</option>
          <option :value="12">近 12 小时</option>
          <option :value="24">近 24 小时</option>
          <option :value="48">近 48 小时</option>
        </select>
      </div>
    </section>

    <section class="content-grid">
      <aside class="zone-panel panel">
        <div class="panel-title">
          <div>
            <p class="eyebrow">分区总览</p>
            <h2>{{ monitoringStore.currentZone?.zone_name || '未选择区域' }}</h2>
          </div>
          <span class="panel-tag">{{ monitoringStore.currentZoneDevices.length }} 台</span>
        </div>
        <div class="zone-metrics">
          <div>
            <span>在线设备</span>
            <strong>{{ monitoringStore.currentZone?.online_count ?? 0 }}</strong>
          </div>
          <div>
            <span>离线设备</span>
            <strong>{{ monitoringStore.currentZone?.offline_count ?? 0 }}</strong>
          </div>
          <div>
            <span>平均 CO2</span>
            <strong>{{ formatMetric(monitoringStore.overview.summary.avg_co2, 'ppm', 0) }}</strong>
          </div>
          <div>
            <span>平均氨气</span>
            <strong>{{ formatMetric(monitoringStore.overview.summary.avg_ammonia, 'ppm', 1) }}</strong>
          </div>
        </div>
        <div class="device-list">
          <button
            v-for="device in monitoringStore.currentZoneDevices"
            :key="device.device_id"
            class="device-card"
            :class="{ active: device.device_id === monitoringStore.selectedDeviceId }"
            @click="selectDevice(device.device_id)"
          >
            <div class="device-card-top">
              <strong>{{ device.device_name }}</strong>
              <span :class="['status-dot', { online: device.is_active }]"></span>
            </div>
            <p>{{ device.location }}</p>
            <small>{{ device.device_id }}</small>
          </button>
        </div>
      </aside>

      <main class="main-panel">
        <div class="panel">
          <EnvironmentDashboard :data="monitoringStore.currentMetrics" />
        </div>
        <div class="panel">
          <TrendChart :title="`${monitoringStore.currentDevice?.device_name || '设备'} 历史趋势`" :data="monitoringStore.historicalData" />
        </div>
        <div class="panel">
          <ControlPanel :device="monitoringStore.currentControlDevice" @command="handleCommand" />
        </div>
        <div class="panel archive-wrap">
          <ArchivePanel
            :summary="monitoringStore.archiveDashboard.summary"
            :archives="monitoringStore.archiveDashboard.archives"
            :selected-archive-id="monitoringStore.selectedArchiveId"
            :selected-archive="monitoringStore.selectedArchive"
            :on-create-archive="handleCreateArchive"
            :on-create-animal="handleCreateAnimal"
            @select="monitoringStore.selectedArchiveId = $event"
          />
        </div>
        <div class="panel">
          <OperationsPanel
            :summary="monitoringStore.operationsDashboard.summary"
            :tasks="monitoringStore.operationsDashboard.tasks"
            :inventory="monitoringStore.operationsDashboard.inventory"
            :assets="monitoringStore.operationsDashboard.assets"
            :archives="monitoringStore.archiveDashboard.archives"
            :users="monitoringStore.users"
            :on-create-task="handleCreateTask"
            :on-update-task-status="handleUpdateTaskStatus"
          />
        </div>
        <div class="panel">
          <SystemPanel
            :summary="monitoringStore.systemDashboard.summary"
            :users="monitoringStore.systemDashboard.users"
            :role-permissions="monitoringStore.systemDashboard.role_permissions"
            :operation-logs="monitoringStore.systemDashboard.operation_logs"
            :on-update-user="handleUpdateUser"
          />
        </div>
      </main>

      <aside class="side-panel">
        <div class="panel">
          <RiskDashboard
            :summary="monitoringStore.riskDashboard.summary"
            :level-distribution="monitoringStore.riskDashboard.level_distribution"
            :zone-distribution="monitoringStore.riskDashboard.zone_distribution"
            :archive-risks="monitoringStore.riskDashboard.archive_risks"
          />
        </div>
        <div class="panel">
          <AlarmList
            :alarms="monitoringStore.alarms"
            :ammonia-alert="monitoringStore.ammoniaAlert"
            @acknowledge="monitoringStore.acknowledgeAlarm"
            @resolve="monitoringStore.resolveAlarm"
          />
        </div>
        <div class="panel">
          <AutomationRules :rules="monitoringStore.controlDashboard.automation_rules" @toggle="monitoringStore.toggleAutomationRule" />
        </div>
        <div class="panel">
          <CommandHistory :commands="monitoringStore.controlDashboard.recent_commands" />
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import AlarmList from './AlarmList.vue'
import ArchivePanel from './ArchivePanel.vue'
import AutomationRules from './AutomationRules.vue'
import CommandHistory from './CommandHistory.vue'
import ControlPanel from './ControlPanel.vue'
import EnvironmentDashboard from './EnvironmentDashboard.vue'
import OperationsPanel from './OperationsPanel.vue'
import RiskDashboard from './RiskDashboard.vue'
import SystemPanel from './SystemPanel.vue'
import TrendChart from './TrendChart.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()
let refreshTimer = null

async function handleZoneChange() {
  const firstDevice = monitoringStore.currentZoneDevices[0]
  if (firstDevice) monitoringStore.selectedDeviceId = firstDevice.device_id
  await monitoringStore.refreshMonitoring()
}

async function handleDeviceChange() {
  await monitoringStore.refreshMonitoring()
}

async function selectDevice(deviceId) {
  monitoringStore.selectedDeviceId = deviceId
  await handleDeviceChange()
}

async function handleCommand(componentKey, commandType, reason) {
  await monitoringStore.executeControlCommand(componentKey, commandType, reason)
}

async function handleCreateArchive(payload) {
  await monitoringStore.createArchive(payload)
}

async function handleCreateAnimal(payload) {
  await monitoringStore.createAnimalProfile(payload)
}

async function handleCreateTask(payload) {
  await monitoringStore.createTask(payload)
}

async function handleUpdateTaskStatus(taskId, status) {
  await monitoringStore.updateTaskStatus(taskId, status)
}

async function handleUpdateUser(userId, payload) {
  await monitoringStore.updateUser(userId, payload)
}

function formatMetric(value, unit, precision = 0) {
  return value === null || value === undefined ? `-- ${unit}` : `${Number(value).toFixed(precision)} ${unit}`
}

onMounted(async () => {
  await monitoringStore.initMonitoring()
  refreshTimer = setInterval(() => {
    monitoringStore.refreshMonitoring()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped lang="scss">
.monitoring-page{min-height:100vh;padding:28px;color:#eff7f8;background:radial-gradient(circle at top right,rgba(88,157,142,.2),transparent 28%),radial-gradient(circle at left center,rgba(246,195,82,.12),transparent 24%),linear-gradient(160deg,#08181d 0%,#102a31 40%,#0a1f25 100%)}
.hero{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;margin-bottom:20px}.hero-copy,.hero-summary,.panel,.status-banner{border-radius:28px;border:1px solid rgba(164,215,210,.14);background:rgba(8,27,32,.78);backdrop-filter:blur(14px)}.hero-copy{padding:28px}.eyebrow{margin:0 0 8px;color:#87a5ac;letter-spacing:.24em;text-transform:uppercase;font-size:12px}h1{margin:0;font-size:34px;line-height:1.2}.hero-text{max-width:760px;margin:14px 0 0;color:#a7bcc1;line-height:1.7}.hero-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:20px}.summary-card{padding:18px;border-radius:20px;background:linear-gradient(180deg,rgba(17,56,63,.9),rgba(10,35,40,.9))}.summary-card span{display:block;color:#94afb2;margin-bottom:8px}.summary-card strong{font-size:28px}
.status-banner{margin-bottom:20px;padding:16px 20px}.status-banner.error{border-color:rgba(255,107,107,.3);background:rgba(56,18,18,.82);color:#ffd3d3}
.toolbar{display:flex;gap:14px;margin-bottom:20px;padding:18px 20px;border-radius:24px;background:rgba(8,27,32,.74);border:1px solid rgba(164,215,210,.12)}.field-group{display:flex;flex-direction:column;gap:8px;min-width:220px}.field-group.compact{min-width:140px}.field-group label{color:#8ca7ad;font-size:13px}.field-group select{height:42px;padding:0 14px;border-radius:14px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.content-grid{display:grid;grid-template-columns:320px minmax(0,1fr) 420px;gap:20px;min-height:calc(100vh - 260px)}.panel{padding:20px}.main-panel,.side-panel{display:grid;gap:20px}.main-panel{grid-template-rows:auto auto auto auto auto auto}.side-panel{grid-template-rows:auto auto auto 1fr}.archive-wrap{overflow:hidden}
.panel-title{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px}.panel-title h2{margin:0;font-size:24px}.panel-tag{padding:6px 12px;border-radius:999px;background:rgba(95,211,188,.12);color:#bfece3}.zone-metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-bottom:18px}.zone-metrics div{padding:14px;border-radius:16px;background:rgba(12,43,49,.78)}.zone-metrics span{display:block;color:#8ca7ad;font-size:12px;margin-bottom:6px}.zone-metrics strong{font-size:20px}
.device-list{display:flex;flex-direction:column;gap:12px}.device-card{text-align:left;padding:14px;border-radius:18px;border:1px solid rgba(164,215,210,.12);background:rgba(7,24,29,.9);color:#eff7f8;cursor:pointer;transition:.2s ease}.device-card.active,.device-card:hover{border-color:rgba(95,211,188,.38);background:rgba(16,54,61,.92)}.device-card-top{display:flex;justify-content:space-between;gap:12px;margin-bottom:8px}.device-card p,.device-card small{margin:0;color:#97afb4}.status-dot{width:10px;height:10px;border-radius:50%;background:#5a6468;margin-top:6px}.status-dot.online{background:#67d5aa;box-shadow:0 0 12px rgba(103,213,170,.5)}
@media (max-width:1400px){.content-grid{grid-template-columns:1fr}.hero{grid-template-columns:1fr}}@media (max-width:900px){.monitoring-page{padding:16px}.toolbar{flex-direction:column}.hero-summary{grid-template-columns:1fr 1fr}}
</style>
