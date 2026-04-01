<template>
  <section class="risk-dashboard">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Risk Alert</p>
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

    <div class="compact-grid">
      <div class="card">
        <h3>等级分布</h3>
        <div class="pill-list">
          <span>严重 {{ levelDistribution.critical ?? 0 }}</span>
          <span>警告 {{ levelDistribution.warning ?? 0 }}</span>
          <span>提示 {{ levelDistribution.info ?? 0 }}</span>
        </div>
      </div>

      <div class="card">
        <h3>区域分布</h3>
        <div v-if="Object.keys(zoneDistribution).length" class="pill-list">
          <span v-for="(count, zone) in zoneDistribution" :key="zone">{{ zone }} {{ count }}</span>
        </div>
        <p v-else class="muted">暂无区域风险数据</p>
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <h3>重点批次风险</h3>
        <span>{{ archiveRisks.length }} 条</span>
      </div>
      <div v-if="archiveRisks.length === 0" class="muted">当前没有需要重点关注的批次。</div>
      <div v-else class="risk-list">
        <article v-for="risk in visibleRisks" :key="risk.batch_number" class="risk-item">
          <strong>{{ risk.batch_number }} / {{ risk.species }}</strong>
          <p>{{ risk.reason }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  levelDistribution: { type: Object, default: () => ({}) },
  zoneDistribution: { type: Object, default: () => ({}) },
  archiveRisks: { type: Array, default: () => [] }
})

const visibleRisks = computed(() => props.archiveRisks.slice(0, 4))
</script>

<style scoped lang="scss">
.risk-dashboard{display:flex;flex-direction:column;gap:14px}
.panel-header{display:flex;justify-content:space-between}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2,h3{margin:0;color:#f3f7fa}
.summary-grid,.compact-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.summary-grid div,.card,.risk-item{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}
.summary-grid span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}
.summary-grid strong{font-size:20px}
.card-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:10px}
.pill-list{display:flex;flex-wrap:wrap;gap:8px}
.pill-list span{padding:6px 10px;border-radius:999px;background:rgba(17,56,63,.9);color:#d7e7ea;font-size:12px}
.card p,.muted,.risk-item p{color:#98b0b5}
.risk-list{display:grid;gap:10px}
@media (max-width:900px){
  .summary-grid,.compact-grid{grid-template-columns:1fr}
}
</style>
