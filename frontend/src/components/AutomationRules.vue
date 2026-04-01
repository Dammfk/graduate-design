<template>
  <section class="rules-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Automation</p>
        <h2>联动策略</h2>
      </div>
      <span class="rule-count">{{ rules.length }} 条</span>
    </div>

    <div class="rule-list">
      <article v-for="rule in rules" :key="rule.id" class="rule-card">
        <div class="rule-main">
          <div>
            <strong>{{ rule.rule_name }}</strong>
            <p>{{ formatMetric(rule.trigger_metric) }} {{ rule.comparison_operator }} {{ rule.threshold_value }} 时 {{ rule.action_command }}</p>
          </div>
          <label class="switch">
            <input :checked="rule.is_enabled" type="checkbox" @change="$emit('toggle', rule.id, $event.target.checked)">
            <span class="slider"></span>
          </label>
        </div>
        <div class="rule-meta">
          <span>{{ rule.target_component }}</span>
          <span>优先级 {{ rule.priority }}</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  rules: { type: Array, default: () => [] }
})

defineEmits(['toggle'])

const metricMap = {
  temperature: '温度',
  humidity: '湿度',
  co2_concentration: 'CO2',
  ammonia_concentration: '氨气'
}

function formatMetric(key) {
  return metricMap[key] || key
}
</script>

<style scoped lang="scss">
.rules-panel{display:flex;flex-direction:column;gap:14px}
.panel-header{display:flex;justify-content:space-between;gap:12px}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2{margin:0;color:#f3f7fa;font-size:22px}
.rule-count{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(255,200,87,.12);color:#ffe2a4}
.rule-list{display:grid;gap:10px;max-height:420px;overflow:auto;padding-right:4px}
.rule-card{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.rule-main{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}
.rule-main p{margin:6px 0 0;color:#97afb4}
.rule-meta{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px}
.rule-meta span{padding:6px 10px;border-radius:999px;background:rgba(17,56,63,.9);color:#d7e7ea;font-size:12px}
.switch{position:relative;width:48px;height:28px;display:inline-block}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;border-radius:999px;background:rgba(126,145,151,.45);transition:.2s}
.slider::before{content:'';position:absolute;width:20px;height:20px;left:4px;top:4px;border-radius:50%;background:#fff;transition:.2s}
input:checked + .slider{background:#4fa98f}
input:checked + .slider::before{transform:translateX(20px)}
</style>
