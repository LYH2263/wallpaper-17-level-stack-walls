<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const openId = ref(null); const detail = ref(null)
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function toggle(r) {
  if (openId.value === r.id) { openId.value = null; detail.value = null; return }
  openId.value = r.id
  detail.value = await getJSON(`/api/runs/${r.id}`)
}
</script>
<template>
  <div class="page"><h1>记录</h1><ul>
  <li v-for="r in items" :key="r.id">
    <template v-if="r.result && r.result.kind === 'floor_stack'">
      <a href="#" @click.prevent="toggle(r)">楼层叠算 · {{ r.result.floors.length }} 层 → {{ r.result.total_rolls }} 卷（{{ r.roll_name }}）</a>
      <div v-if="openId === r.id && detail" class="floor-detail">
        <div v-for="(f, i) in detail.result.floors" :key="i">
          <strong>{{ f.floor || `第${i + 1}层` }}</strong>：小计 {{ f.rolls }} 卷
          <ul><li v-for="w in f.walls" :key="w.wall_id">{{ w.name }} — {{ w.drops }} 条 × {{ w.drop_len_m }}m → {{ w.rolls }} 卷</li></ul>
        </div>
        <p>总卷数：{{ detail.result.total_rolls }} 卷</p>
      </div>
    </template>
    <span v-else>{{ r.wall_name }} → {{ r.result?.rolls }} 卷</span>
  </li>
  </ul></div>
</template>
