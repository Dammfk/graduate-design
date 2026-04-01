<template>
  <section class="history-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">控制留痕</p>
        <h2>近期命令记录</h2>
      </div>
      <span class="history-count">{{ commands.length }}</span>
    </div>

    <div v-if="commands.length === 0" class="empty-state">暂无控制记录。</div>

    <div v-else class="history-list">
      <article v-for="command in commands" :key="command.id" class="history-card">
        <div class="history-top">
          <strong>{{ command.device_name || command.device_id }}</strong>
          <span class="mode">{{ command.execution_mode === 'auto' ? '自动' : '手动' }}</span>
        </div>
        <p>{{ command.target_component }} / {{ command.command_type }}</p>
        <small>{{ command.reason || '无说明' }}</small>
        <time>{{ formatTime(command.executed_at) }}</time>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  commands: { type: Array, default: () => [] }
})

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}
</script>

<style scoped lang="scss">
.history-panel {
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

.history-count {
  align-self: flex-start;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(95, 211, 188, 0.12);
  color: #bfece3;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-card,
.empty-state {
  padding: 16px;
  border-radius: 18px;
  background: rgba(10, 33, 39, 0.88);
  border: 1px solid rgba(164, 215, 210, 0.1);
}

.history-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.mode {
  color: #ffe2a4;
}

.history-card p,
.history-card small,
.history-card time {
  display: block;
  margin-top: 8px;
  color: #97afb4;
}
</style>
