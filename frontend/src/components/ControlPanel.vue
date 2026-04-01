<template>
  <section class="control-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">设备控制</p>
        <h2>{{ device?.device_name || '设备控制面板' }}</h2>
      </div>
      <span class="zone-badge">{{ device?.zone_name || '未选择区域' }}</span>
    </div>

    <div v-if="!device" class="empty-state">请先选择设备，再查看控制状态。</div>

    <template v-else>
      <div class="env-snapshot">
        <div>
          <span>温度</span>
          <strong>{{ formatValue(device.latest_environment?.temperature, '°C', 1) }}</strong>
        </div>
        <div>
          <span>湿度</span>
          <strong>{{ formatValue(device.latest_environment?.humidity, '%', 1) }}</strong>
        </div>
        <div>
          <span>CO2</span>
          <strong>{{ formatValue(device.latest_environment?.co2_concentration, 'ppm', 0) }}</strong>
        </div>
        <div>
          <span>氨气</span>
          <strong>{{ formatValue(device.latest_environment?.ammonia_concentration, 'ppm', 1) }}</strong>
        </div>
      </div>

      <div class="component-list">
        <article v-for="component in device.components" :key="component.component_key" class="component-card">
          <div class="component-info">
            <strong>{{ component.component_name }}</strong>
            <p>当前状态：<span :class="['status-text', component.status === 'ON' ? 'on' : 'off']">{{ component.status }}</span></p>
            <small>工作模式：{{ component.mode === 'auto' ? '自动联动' : '手动优先' }}</small>
          </div>
          <div class="component-actions">
            <button class="ghost-btn" @click="$emit('command', component.component_key, 'OFF', `手动关闭${component.component_name}`)">
              关闭
            </button>
            <button class="primary-btn" @click="$emit('command', component.component_key, 'ON', `手动开启${component.component_name}`)">
              开启
            </button>
          </div>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
defineProps({
  device: { type: Object, default: null }
})

defineEmits(['command'])

function formatValue(value, unit, precision) {
  if (value === null || value === undefined) return `-- ${unit}`
  return `${Number(value).toFixed(precision)} ${unit}`
}
</script>

<style scoped lang="scss">
.control-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #87a5ac;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: #f3f7fa;
  font-size: 24px;
}

.zone-badge {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(95, 211, 188, 0.12);
  color: #bfece3;
}

.empty-state {
  padding: 28px;
  border-radius: 18px;
  background: rgba(10, 33, 39, 0.8);
  color: #95abb0;
}

.env-snapshot {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.env-snapshot div,
.component-card {
  padding: 14px;
  border-radius: 16px;
  background: rgba(10, 33, 39, 0.88);
}

.env-snapshot span {
  display: block;
  color: #87a5ac;
  font-size: 12px;
  margin-bottom: 6px;
}

.env-snapshot strong {
  font-size: 20px;
}

.component-list {
  display: grid;
  gap: 12px;
}

.component-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  border: 1px solid rgba(164, 215, 210, 0.1);
}

.component-info p,
.component-info small {
  color: #97afb4;
}

.status-text.on {
  color: #9cd8be;
}

.status-text.off {
  color: #c7d5d9;
}

.component-actions {
  display: flex;
  gap: 10px;
}

.ghost-btn,
.primary-btn {
  height: 38px;
  min-width: 72px;
  border-radius: 12px;
  cursor: pointer;
}

.ghost-btn {
  border: 1px solid rgba(164, 215, 210, 0.22);
  background: transparent;
  color: #d7e8eb;
}

.primary-btn {
  border: none;
  background: linear-gradient(135deg, #4fa98f, #2f7f6d);
  color: white;
}

@media (max-width: 900px) {
  .env-snapshot {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .component-card {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
