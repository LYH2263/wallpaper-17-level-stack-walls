<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'
import FloorPicker from '../components/FloorPicker.vue'
const walls = ref([]); const rolls = ref([]); const wallId = ref(1); const rollId = ref(1); const out = ref(null)
const floors = ref([{ floor: '1F', wall_ids: [] }])
const stackRollId = ref(1); const stackOut = ref(null); const stackErr = ref('')
onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality==='clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality==='clean')
  if (walls.value.length) wallId.value = walls.value[0].id
  if (rolls.value.length) { rollId.value = rolls.value[0].id; stackRollId.value = rolls.value[0].id }
})
async function run(save) {
  out.value = save ? await postJSON('/api/estimate', { wall_id: wallId.value, roll_id: rollId.value, save: true }) : await getJSON(`/api/estimate?wall_id=${wallId.value}&roll_id=${rollId.value}`)
}
async function runStack(save) {
  stackErr.value = ''; stackOut.value = null
  try {
    stackOut.value = await postJSON('/api/estimate/floors', { roll_id: stackRollId.value, floors: floors.value, save })
  } catch (e) { stackErr.value = String(e && e.message ? e.message : e) }
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
  <select v-model.number="stackRollId"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <FloorPicker v-model="floors" :walls="walls" />
  <button @click="runStack(false)">试算</button><button @click="runStack(true)">保存</button>
  <p v-if="stackErr" class="warn">{{ stackErr }}</p>
  <div v-if="stackOut"><strong>总卷数 {{ stackOut.total_rolls }} 卷</strong>
  <div v-for="(f, i) in stackOut.floors" :key="i">{{ f.floor || `第${i + 1}层` }}：{{ f.walls.length }} 面墙，小计 {{ f.rolls }} 卷</div></div>
  </div>
</template>
