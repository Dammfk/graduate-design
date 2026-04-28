<template>
  <div class="alarms-layout">
    <section class="page-panel">
      <RiskDashboard
        :summary="monitoringStore.riskDashboard.summary"
        :level-distribution="monitoringStore.riskDashboard.level_distribution"
        :zone-distribution="monitoringStore.riskDashboard.zone_distribution"
        :archive-risks="monitoringStore.riskDashboard.archive_risks"
      />
    </section>

    <section class="page-panel">
      <AlarmList
        :alarms="monitoringStore.alarms"
        :ammonia-alert="monitoringStore.ammoniaAlert"
        :busy-alarm-id="busyAlarmId"
        :busy-action="busyAction"
        :action-message="actionMessage"
        @acknowledge="handleAcknowledge"
        @resolve="handleResolve"
      />
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AlarmList from '../components/AlarmList.vue'
import RiskDashboard from '../components/RiskDashboard.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()
const busyAlarmId = ref(null)
const busyAction = ref('')
const actionMessage = ref(null)
let messageTimer = null

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
</script>

<style scoped lang="scss">
.alarms-layout {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 14px;
}

@media (max-width: 1100px) {
  .alarms-layout {
    grid-template-columns: 1fr;
  }
}
</style>
