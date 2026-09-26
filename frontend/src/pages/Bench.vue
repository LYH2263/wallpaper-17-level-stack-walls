<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'
import FloorPicker from '../components/FloorPicker.vue'
const walls = ref([]); const rolls = ref([]); const wallId = ref(1); const rollId = ref(1); const out = ref(null)
const floors = ref([]); const stackOut = ref(null); const stackErr = ref('')
onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality==='clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality==='clean')
  if (walls.value.length) wallId.value = walls.value[0].id
  if (rolls.value.length) rollId.value = rolls.value[0].id
})
async function run(save) {
  out.value = save ? await postJSON('/api/estimate', { wall_id: wallId.value, roll_id: rollId.value, save: true }) : await getJSON(`/api/estimate?wall_id=${wallId.value}&roll_id=${rollId.value}`)
}
async function runStack(save) {
  stackErr.value = ''; stackOut.value = null
  try {
    stackOut.value = await postJSON('/api/estimate/stack', { roll_id: rollId.value, floors: floors.value, save })
  } catch (e) {
    let msg = e.message
    try { msg = JSON.parse(e.message).detail || msg } catch {}
    stackErr.value = `叠算失败：${msg}`
  }
}
</script>
<template>
  <div class="page"><h1>算卷工作台</h1>
  <select v-model.number="wallId"><option v-for="w in walls" :key="w.id" :value="w.id">{{ w.name }}</option></select>
  <select v-model.number="rollId"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <button @click="run(false)">试算</button><button @click="run(true)">保存</button>
  <div v-if="out"><strong>{{ out.rolls }} 卷</strong> · {{ out.drops }} 条 · 每条 {{ out.drop_len_m }}m
  <DropStripBar :drops="out.drops" :drop-len="out.drop_len_m" :rolls="out.rolls" /></div>

  <h2>楼层叠算</h2>
  <FloorPicker v-model="floors" :walls="walls" />
  <button :disabled="!floors.length" @click="runStack(false)">叠算试算</button>
  <button :disabled="!floors.length" @click="runStack(true)">保存叠算</button>
  <p v-if="stackErr" class="warn">{{ stackErr }}</p>
  <div v-if="stackOut">
    <div v-for="f in stackOut.floors" :key="f.floor">{{ f.floor }}：{{ f.subtotal_rolls }} 卷（{{ f.walls.length }} 面墙）</div>
    <strong>合计 {{ stackOut.total_rolls }} 卷</strong>
    <p v-if="stackOut.run_id">已保存记录 #{{ stackOut.run_id }}</p>
  </div>
  </div>
</template>
