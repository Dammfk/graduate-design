<template>
  <section class="alarm-settings">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Alert Controls</p>
        <h3>预警设置</h3>
      </div>
      <span class="hint">修改后立即生效</span>
    </div>

    <div class="setting-list">
      <article v-for="item in settings" :key="item.alarm_type" class="setting-item">
        <div class="setting-main">
          <div>
            <strong>{{ item.alarm_label }}</strong>
            <p>{{ formatLevel(item.alarm_level) }} · 类型 {{ item.alarm_type }}</p>
          </div>
          <label class="switch">
            <input
              type="checkbox"
              :checked="item.is_enabled"
              :disabled="busyKey === item.alarm_type"
              @change="handleToggle(item, $event)"
            >
            <span class="slider"></span>
          </label>
        </div>

        <div class="setting-controls">
          <label class="threshold-field">
            <span>阈值</span>
            <div class="threshold-input-wrap">
              <input
                :value="drafts[item.alarm_type]"
                type="number"
                step="0.1"
                :disabled="busyKey === item.alarm_type"
                @input="drafts[item.alarm_type] = $event.target.value"
              >
              <small>{{ formatUnit(item.alarm_type) }}</small>
            </div>
          </label>
          <button
            class="save-btn"
            :disabled="busyKey === item.alarm_type"
            @click="handleSave(item)"
          >
            {{ busyKey === item.alarm_type ? '保存中...' : '保存阈值' }}
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  settings: { type: Array, default: () => [] },
  busyKey: { type: String, default: '' }
})

const emit = defineEmits(['update-setting'])
const drafts = reactive({})

watch(
  () => props.settings,
  (list) => {
    for (const item of list) {
      drafts[item.alarm_type] = item.threshold_value
    }
  },
  { immediate: true, deep: true }
)

function formatLevel(level) {
  if (level === 'critical') return '严重'
  if (level === 'warning') return '警告'
  return '提示'
}

function formatUnit(alarmType) {
  if (alarmType.startsWith('temperature')) return '°C'
  if (alarmType.startsWith('humidity')) return '%'
  return 'ppm'
}

function handleToggle(item, event) {
  emit('update-setting', item.alarm_type, {
    is_enabled: event.target.checked
  })
}

function handleSave(item) {
  emit('update-setting', item.alarm_type, {
    threshold_value: Number(drafts[item.alarm_type])
  })
}
</script>

<style scoped lang="scss">
.alarm-settings{display:flex;flex-direction:column;gap:14px;padding:16px;border-radius:20px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.14)}
.panel-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h3{margin:0;color:#f3f7fa}
.hint{padding:6px 10px;border-radius:999px;background:rgba(17,56,63,.9);color:#d7e7ea;font-size:13px}
.setting-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.setting-item{padding:14px;border-radius:16px;background:rgba(7,25,29,.9);border:1px solid rgba(164,215,210,.12)}
.setting-main{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px}
.setting-main strong{display:block;color:#f5fbfc;font-size:17px;margin-bottom:4px}
.setting-main p{margin:0;color:#97aeb4;font-size:14px}
.setting-controls{display:flex;gap:10px;align-items:end;flex-wrap:wrap}
.threshold-field{display:flex;flex-direction:column;gap:6px}
.setting-controls span{color:#9fb3b8;font-size:13px}
.threshold-input-wrap{display:flex;align-items:center;gap:8px;height:38px;padding:0 10px;border-radius:10px;border:1px solid rgba(164,215,210,.16);background:rgba(12,42,48,.95)}
.threshold-input-wrap input{height:100%;width:68px;padding:0;border:none;background:transparent;color:#eef5f7;font-size:15px;font-weight:600}
.threshold-input-wrap input:focus{outline:none}
.threshold-input-wrap small{min-width:30px;color:#87a5ac;font-size:12px;text-align:right}
.save-btn{height:38px;padding:0 12px;border:none;border-radius:10px;background:linear-gradient(135deg,#54d3c2,#6fe0b6);color:#082126;font-weight:700;font-size:13px;cursor:pointer;white-space:nowrap}
.save-btn:disabled{opacity:.65;cursor:wait}
.switch{position:relative;width:48px;height:28px;display:inline-block;flex:0 0 auto}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;border-radius:999px;background:rgba(126,145,151,.45);transition:.2s}
.slider::before{content:'';position:absolute;width:20px;height:20px;left:4px;top:4px;border-radius:50%;background:#fff;transition:.2s}
.switch input:checked + .slider{background:#4fa98f}
.switch input:checked + .slider::before{transform:translateX(20px)}
.switch input:disabled + .slider{opacity:.65}
@media (max-width:900px){
  .setting-list{grid-template-columns:1fr}
  .setting-main{flex-direction:column}
}
</style>
