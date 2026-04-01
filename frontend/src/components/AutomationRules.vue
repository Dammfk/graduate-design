<template>
  <section class="rules-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">自动控制</p>
        <h2>联动策略</h2>
      </div>
      <span class="rule-count">{{ rules.length }} 条</span>
    </div>

    <div class="rule-list">
      <article v-for="rule in rules" :key="rule.id" class="rule-card">
        <div class="rule-top">
          <div>
            <strong>{{ rule.rule_name }}</strong>
            <p>{{ rule.description }}</p>
          </div>
          <label class="switch">
            <input :checked="rule.is_enabled" type="checkbox" @change="$emit('toggle', rule.id, $event.target.checked)">
            <span class="slider"></span>
          </label>
        </div>
        <div class="rule-meta">
          <span>组件：{{ rule.target_component }}</span>
          <span>条件：{{ formatMetric(rule.trigger_metric) }} {{ rule.comparison_operator }} {{ rule.threshold_value }}</span>
          <span>动作：{{ rule.action_command }}</span>
          <span>优先级：{{ rule.priority }}</span>
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
.rules-panel {
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

.rule-count {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 200, 87, 0.12);
  color: #ffe2a4;
}

.rule-list {
  display: grid;
  gap: 12px;
}

.rule-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(10, 33, 39, 0.88);
  border: 1px solid rgba(164, 215, 210, 0.1);
}

.rule-top {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.rule-top p {
  margin: 6px 0 0;
  color: #97afb4;
}

.rule-meta {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.rule-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 56, 63, 0.9);
  color: #d7e7ea;
  font-size: 12px;
}

.switch {
  position: relative;
  width: 48px;
  height: 28px;
  display: inline-block;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: rgba(126, 145, 151, 0.45);
  transition: 0.2s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 4px;
  top: 4px;
  border-radius: 50%;
  background: white;
  transition: 0.2s;
}

input:checked + .slider {
  background: #4fa98f;
}

input:checked + .slider::before {
  transform: translateX(20px);
}
</style>
