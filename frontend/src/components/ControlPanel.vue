<template>
  <section class="control-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Device Control</p>
        <h2>{{ device?.device_name || '设备控制面板' }}</h2>
      </div>
      <span class="zone-badge">{{ device?.zone_name || '未选择区域' }}</span>
    </div>

    <div v-if="!device" class="empty-state">请先选择设备，再查看控制状态。</div>

    <template v-else>
      <div class="control-grid">
        <div class="snapshot-card">
          <h3>环境快照</h3>
          <div class="env-snapshot compact">
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
        </div>

        <div class="action-card">
          <h3>设备组件</h3>
          <div class="component-list">
            <article v-for="component in device.components" :key="component.component_key" class="component-card">
              <div class="component-info">
                <strong>{{ component.component_name }}</strong>
                <p>
                  当前状态：
                  <span :class="['status-text', component.status === 'ON' ? 'on' : 'off']">
                    {{ component.status === 'ON' ? '开启' : '关闭' }}
                  </span>
                </p>
                <small>模式：{{ component.mode === 'auto' ? '自动联动' : '手动优先' }}</small>
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
        </div>
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
.control-panel{display:flex;flex-direction:column;gap:14px}
.panel-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2,h3{margin:0;color:#f3f7fa}
.zone-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(95,211,188,.12);color:#bfece3}
.empty-state{padding:22px;border-radius:16px;background:rgba(10,33,39,.8);color:#95abb0}
.control-grid{display:grid;grid-template-columns:240px minmax(0,1fr);gap:12px}
.snapshot-card,.action-card,.component-card{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.env-snapshot{display:grid;gap:10px}
.env-snapshot.compact{grid-template-columns:repeat(2,minmax(0,1fr))}
.env-snapshot span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}
.env-snapshot strong{font-size:18px}
.component-list{display:grid;gap:10px}
.component-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center}
.component-info p,.component-info small{margin:4px 0 0;color:#97afb4}
.status-text.on{color:#9cd8be}
.status-text.off{color:#c7d5d9}
.component-actions{display:flex;gap:8px}
.ghost-btn,.primary-btn{height:36px;min-width:68px;border-radius:10px;cursor:pointer}
.ghost-btn{border:1px solid rgba(164,215,210,.22);background:transparent;color:#d7e8eb}
.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}
@media (max-width:900px){
  .control-grid{grid-template-columns:1fr}
  .component-card{grid-template-columns:1fr}
}
</style>
