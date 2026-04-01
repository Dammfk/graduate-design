<template>
  <section class="risk-dashboard">
    <div class="panel-header">
      <div>
        <p class="eyebrow">风险预警</p>
        <h2>风险摘要</h2>
      </div>
    </div>

    <div class="summary-grid">
      <div>
        <span>告警总数</span>
        <strong>{{ summary.total_alarms ?? 0 }}</strong>
      </div>
      <div>
        <span>待处理</span>
        <strong>{{ summary.pending_alarms ?? 0 }}</strong>
      </div>
      <div>
        <span>24h 严重预警</span>
        <strong>{{ summary.critical_alarms_24h ?? 0 }}</strong>
      </div>
      <div>
        <span>高风险区域</span>
        <strong>{{ summary.highest_risk_zone || '--' }}</strong>
      </div>
    </div>

    <div class="distribution-grid">
      <div class="card">
        <h3>等级分布</h3>
        <p>严重：{{ levelDistribution.critical ?? 0 }}</p>
        <p>警告：{{ levelDistribution.warning ?? 0 }}</p>
        <p>提示：{{ levelDistribution.info ?? 0 }}</p>
      </div>

      <div class="card">
        <h3>区域分布</h3>
        <p v-for="(count, zone) in zoneDistribution" :key="zone">{{ zone }}：{{ count }}</p>
        <p v-if="Object.keys(zoneDistribution).length === 0">暂无区域风险数据</p>
      </div>
    </div>

    <div class="card">
      <h3>重点批次风险</h3>
      <div v-if="archiveRisks.length === 0" class="muted">当前没有需要重点关注的批次。</div>
      <div v-else class="risk-list">
        <article v-for="risk in archiveRisks" :key="risk.batch_number" class="risk-item">
          <strong>{{ risk.batch_number }} / {{ risk.species }}</strong>
          <p>{{ risk.reason }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  summary: { type: Object, default: () => ({}) },
  levelDistribution: { type: Object, default: () => ({}) },
  zoneDistribution: { type: Object, default: () => ({}) },
  archiveRisks: { type: Array, default: () => [] }
})
</script>

<style scoped lang="scss">
.risk-dashboard { display:flex; flex-direction:column; gap:16px; }
.panel-header { display:flex; justify-content:space-between; }
.eyebrow { margin:0 0 6px; color:#87a5ac; font-size:12px; letter-spacing:.2em; text-transform:uppercase; }
h2,h3 { margin:0; color:#f3f7fa; }
.summary-grid,.distribution-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
.summary-grid div,.card,.risk-item { padding:14px; border-radius:16px; background:rgba(10,33,39,.88); }
.summary-grid span { display:block; color:#87a5ac; font-size:12px; margin-bottom:6px; }
.summary-grid strong { font-size:20px; }
.card p,.muted,.risk-item p { color:#98b0b5; }
.risk-list { display:grid; gap:10px; margin-top:10px; }
</style>
