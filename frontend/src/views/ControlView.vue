<template>
  <div class="page-grid">
    <ModuleContextBar
      :zone-options="monitoringStore.zoneOptions"
      :devices="monitoringStore.currentZoneDevices"
      :selected-zone="monitoringStore.selectedZone"
      :selected-device-id="monitoringStore.selectedDeviceId"
      @update:zone="handleZoneChange"
      @update:device="handleDeviceChange"
    />

    <section class="control-layout">
      <section class="page-panel control-main-panel">
        <ControlPanel
          :device="monitoringStore.currentControlDevice"
          :busy-map="monitoringStore.commandInFlightByComponent"
          :last-feedback="monitoringStore.lastControlFeedback"
          @command="handleCommand"
        />
      </section>

      <div class="control-side-stack">
        <section class="page-panel side-panel">
          <AutomationRules :rules="monitoringStore.controlDashboard.automation_rules" @toggle="monitoringStore.toggleAutomationRule" />
        </section>

        <section class="page-panel side-panel">
          <div class="history-preview">
            <div class="history-preview__header">
              <div>
                <p class="eyebrow">Command History</p>
                <h3>近期控制记录</h3>
              </div>
              <span class="history-preview__count">{{ commands.length }} 条</span>
            </div>

            <div v-if="previewCommands.length === 0" class="history-preview__empty">
              暂无控制记录。
            </div>

            <div v-else class="history-preview__list">
              <article v-for="command in previewCommands" :key="command.id" class="history-preview__card">
                <div class="history-preview__top">
                  <strong>{{ command.device_name || command.device_id }}</strong>
                  <span :class="['history-preview__status', mapStatusTone(command.status)]">
                    {{ formatLocalStatus(command.status) }}
                  </span>
                </div>
                <p>{{ formatTarget(command.target_component) }} / {{ formatCommand(command.command_type) }}</p>
                <small>{{ command.reason || '无说明' }}</small>
                <time>{{ formatTime(command.executed_at) }}</time>
              </article>
            </div>

            <button
              v-if="commands.length > previewLimit"
              type="button"
              class="history-preview__more"
              @click="showHistoryModal = true"
            >
              显示更多
            </button>
          </div>
        </section>
      </div>
    </section>

    <teleport to="body">
      <div v-if="showHistoryModal" class="history-modal" @click.self="showHistoryModal = false">
        <div class="history-modal__card">
          <div class="history-modal__header">
            <div>
              <p class="eyebrow">Command History</p>
              <h3>近期控制记录</h3>
            </div>
            <button type="button" class="history-modal__close" @click="showHistoryModal = false">关闭</button>
          </div>
          <CommandHistory :commands="commands" />
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AutomationRules from '../components/AutomationRules.vue'
import CommandHistory from '../components/CommandHistory.vue'
import ControlPanel from '../components/ControlPanel.vue'
import ModuleContextBar from '../components/ModuleContextBar.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()
const showHistoryModal = ref(false)
const previewLimit = 3

const commands = computed(() => monitoringStore.controlDashboard.recent_commands || [])
const previewCommands = computed(() => commands.value.slice(0, previewLimit))

async function handleZoneChange(zoneName) {
  monitoringStore.selectedZone = zoneName
  const firstDevice = monitoringStore.currentZoneDevices[0]
  if (firstDevice) {
    monitoringStore.selectedDeviceId = firstDevice.device_id
  }
  await monitoringStore.loadModule('control')
}

async function handleDeviceChange(deviceId) {
  monitoringStore.selectedDeviceId = deviceId
  await monitoringStore.fetchControlDashboard()
}

async function handleCommand(componentKey, commandType, reason) {
  try {
    await monitoringStore.executeControlCommand(componentKey, commandType, reason)
  } catch (error) {
    console.error('Control command failed', error)
  }
}

const targetLabelMap = {
  fan: '风机',
  cooling_pad: '水帘',
  fill_light: '补光灯'
}

function formatTarget(target) {
  return targetLabelMap[target] || target || '--'
}

function formatCommand(commandType) {
  if (commandType === 'ON') return '开启'
  if (commandType === 'OFF') return '关闭'
  return commandType || '--'
}

function formatLocalStatus(status) {
  if (status === 'sent') return '已送达'
  if (status === 'success') return '已执行'
  if (status === 'failed') return '失败'
  return '已保存'
}

function mapStatusTone(status) {
  if (status === 'failed') return 'failed'
  if (status === 'sent' || status === 'success') return 'success'
  return 'pending'
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}
</script>

<style scoped lang="scss">
.control-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(320px, 0.88fr);
  gap: 14px;
  align-items: start;
}

.control-main-panel {
  min-height: 0;
}

.control-side-stack {
  display: grid;
  grid-template-rows: auto auto;
  gap: 14px;
  align-content: start;
}

.side-panel {
  min-height: 0;
}

.history-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.eyebrow {
  margin: 0 0 6px;
  color: #87a5ac;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.history-preview__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.history-preview__header h3,
.history-modal__header h3 {
  margin: 0;
  color: #f3f7fa;
  font-size: 22px;
}

.history-preview__count {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(95, 211, 188, 0.12);
  color: #bfece3;
  font-size: 14px;
}

.history-preview__empty {
  padding: 14px;
  border-radius: 16px;
  background: rgba(10, 33, 39, 0.88);
  border: 1px solid rgba(164, 215, 210, 0.1);
  color: #97afb4;
}

.history-preview__list {
  display: grid;
  gap: 10px;
  min-height: 0;
  max-height: 280px;
  overflow: auto;
}

.history-preview__card {
  padding: 14px;
  border-radius: 16px;
  background: rgba(10, 33, 39, 0.88);
  border: 1px solid rgba(164, 215, 210, 0.1);
}

.history-preview__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.history-preview__card p,
.history-preview__card small,
.history-preview__card time {
  display: block;
  margin-top: 8px;
  color: #97afb4;
}

.history-preview__card p {
  font-size: 16px;
  font-weight: 600;
  color: #f2f7f9;
}

.history-preview__status {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 13px;
}

.history-preview__status.pending {
  background: rgba(255, 200, 87, 0.12);
  color: #ffe2a4;
}

.history-preview__status.success {
  background: rgba(95, 211, 188, 0.12);
  color: #bfece3;
}

.history-preview__status.failed {
  background: rgba(255, 120, 120, 0.12);
  color: #ffc2c2;
}

.history-preview__more,
.history-modal__close {
  align-self: flex-start;
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid rgba(164, 215, 210, 0.22);
  background: rgba(14, 44, 52, 0.82);
  color: #d7e8eb;
  cursor: pointer;
  transition: 0.2s ease;
}

.history-preview__more:hover,
.history-modal__close:hover {
  background: rgba(18, 56, 64, 0.94);
  border-color: rgba(164, 215, 210, 0.3);
}

.history-modal {
  position: fixed;
  inset: 0;
  z-index: 1400;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(4, 11, 14, 0.68);
  backdrop-filter: blur(10px);
}

.history-modal__card {
  width: min(1180px, 100%);
  max-height: min(84vh, 900px);
  overflow: auto;
  padding: 20px;
  border-radius: 24px;
  background: rgba(8, 25, 30, 0.98);
  border: 1px solid rgba(164, 215, 210, 0.14);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.history-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

:deep(.toolbar-card) {
  padding: 14px 16px;
  gap: 10px;
  align-items: end;
}

:deep(.toolbar-field) {
  min-width: 0;
  flex: 0 1 280px;
}

:deep(.toolbar-field label) {
  font-size: 13px;
  margin-bottom: 2px;
}

:deep(.toolbar-field select) {
  height: 40px;
}

:deep(.rules-panel) {
  gap: 12px;
}

:deep(.rules-panel .panel-header) {
  align-items: flex-start;
}

:deep(.rules-panel .rule-list) {
  max-height: 300px;
}

@media (max-width: 1320px) {
  .control-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .history-modal {
    padding: 14px;
    align-items: flex-end;
  }

  .history-modal__card {
    width: 100%;
    max-height: 88vh;
    border-radius: 22px 22px 0 0;
  }
}
</style>
