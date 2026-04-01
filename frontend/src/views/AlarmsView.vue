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
        @acknowledge="monitoringStore.acknowledgeAlarm"
        @resolve="monitoringStore.resolveAlarm"
      />
    </section>
  </div>
</template>

<script setup>
import AlarmList from '../components/AlarmList.vue'
import RiskDashboard from '../components/RiskDashboard.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()
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
