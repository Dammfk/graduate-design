<template>
  <div class="alarms-layout">
    <section class="page-panel">
      <template v-if="hasRiskData">
        <RiskDashboard
          :summary="monitoringStore.riskDashboard.summary"
          :level-distribution="monitoringStore.riskDashboard.level_distribution"
          :zone-distribution="monitoringStore.riskDashboard.zone_distribution"
          :archive-risks="monitoringStore.riskDashboard.archive_risks"
        />
      </template>
      <div v-else class="panel-empty-state">
        <strong>风险摘要暂时为空</strong>
        <span>当前还没有新的告警统计结果。可以等待设备继续上报，或先调整预警阈值后再观察变化。</span>
      </div>

      <AlarmSettings
        :settings="monitoringStore.alarmSettings"
        :busy-key="busySettingKey"
        @update-setting="handleUpdateSetting"
      />
    </section>

    <section class="page-panel">
      <template v-if="monitoringStore.alarms.length">
        <AlarmList
          :alarms="monitoringStore.alarms"
          :ammonia-alert="monitoringStore.ammoniaAlert"
          :busy-alarm-id="busyAlarmId"
          :busy-action="busyAction"
          :action-message="actionMessage"
          @acknowledge="handleAcknowledge"
          @resolve="handleResolve"
        />
      </template>
      <div v-else class="panel-empty-state alarms-empty">
        <strong>当前没有待处理告警</strong>
        <span>环境指标目前处于正常范围内。后续如有新的异常上报，这里会优先出现待处理告警。</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AlarmList from '../components/AlarmList.vue'
import AlarmSettings from '../components/AlarmSettings.vue'
import RiskDashboard from '../components/RiskDashboard.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()
const busyAlarmId = ref(null)
const busyAction = ref('')
const actionMessage = ref(null)
const busySettingKey = ref('')
let messageTimer = null

const hasRiskData = computed(() => {
  const summary = monitoringStore.riskDashboard.summary || {}
  return (
    Number(summary.pending_count || 0) > 0 ||
    Number(summary.total_count || 0) > 0 ||
    Number(summary.critical_count || 0) > 0 ||
    Object.keys(monitoringStore.riskDashboard.level_distribution || {}).length > 0 ||
    Object.keys(monitoringStore.riskDashboard.zone_distribution || {}).length > 0 ||
    (monitoringStore.riskDashboard.archive_risks || []).length > 0
  )
})

function showMessage(type, text) {
  actionMessage.value = { type, text }
  if (messageTimer) {
    window.clearTimeout(messageTimer)
  }
  messageTimer = window.setTimeout(() => {
    actionMessage.value = null
  }, 3000)
}

async function handleAcknowledge(alarmId) {
  busyAlarmId.value = alarmId
  busyAction.value = 'acknowledge'
  try {
    await monitoringStore.acknowledgeAlarm(alarmId)
    showMessage('success', `告警 #${alarmId} 已确认`)
  } catch (error) {
    showMessage('error', error?.response?.data?.detail || error?.message || '告警确认失败')
  } finally {
    busyAlarmId.value = null
    busyAction.value = ''
  }
}

async function handleResolve(alarmId) {
  busyAlarmId.value = alarmId
  busyAction.value = 'resolve'
  try {
    await monitoringStore.resolveAlarm(alarmId)
    showMessage('success', `告警 #${alarmId} 已解决`)
  } catch (error) {
    showMessage('error', error?.response?.data?.detail || error?.message || '告警解决失败')
  } finally {
    busyAlarmId.value = null
    busyAction.value = ''
  }
}

async function handleUpdateSetting(alarmType, payload) {
  busySettingKey.value = alarmType
  try {
    await monitoringStore.updateAlarmSetting(alarmType, payload)
    showMessage('success', `预警设置 ${alarmType} 已更新`)
  } catch (error) {
    showMessage('error', error?.response?.data?.detail || error?.message || '预警设置更新失败')
  } finally {
    busySettingKey.value = ''
  }
}
</script>

<style scoped lang="scss">
.alarms-layout {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 14px;
}

.panel-empty-state {
  display: grid;
  gap: 8px;
  align-content: center;
  min-height: 240px;
  padding: 22px;
  border-radius: 18px;
  border: 1px dashed rgba(164, 215, 210, 0.16);
  background: rgba(9, 29, 35, 0.74);
}

.panel-empty-state strong {
  font-size: 18px;
  color: #eef7f7;
}

.panel-empty-state span {
  color: var(--text-muted);
  line-height: 1.7;
}

.alarms-empty {
  min-height: 100%;
}

@media (max-width: 1360px) {
  .alarms-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .alarms-layout {
    grid-template-columns: 1fr;
  }
}
</style>
