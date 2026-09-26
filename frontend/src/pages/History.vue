<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const openId = ref(null); const detail = ref(null)
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
async function toggle(r) {
  if (openId.value === r.id) { openId.value = null; detail.value = null; return }
  detail.value = await getJSON(`/api/runs/${r.id}`)
  openId.value = r.id
}
</script>
<template>
  <div class="page"><h1>记录</h1><ul>
    <li v-for="r in items" :key="r.id">
      <a href="#" @click.prevent="toggle(r)">
        <template v-if="r.result?.kind === 'floor_stack'">楼层叠算（{{ r.result.floors.length }} 层）→ {{ r.result.total_rolls }} 卷</template>
        <template v-else>{{ r.wall_name }} → {{ r.result?.rolls }} 卷</template>
      </a>
      <div v-if="openId === r.id && detail" class="run-detail">
        <template v-if="detail.result?.kind === 'floor_stack'">
          <div v-for="f in detail.result.floors" :key="f.floor">
            <strong>{{ f.floor }}</strong>：{{ f.subtotal_rolls }} 卷
            <ul><li v-for="w in f.walls" :key="w.wall_id">{{ w.name }} · 周长 {{ w.perimeter }}m · {{ w.rolls }} 卷</li></ul>
          </div>
          <div>总卷数：{{ detail.result.total_rolls }} 卷 · 卷材 {{ detail.result.roll_name }}</div>
        </template>
        <template v-else>{{ detail.wall_name }} → {{ detail.result?.rolls }} 卷 · {{ detail.result?.drops }} 条</template>
      </div>
    </li>
  </ul></div>
</template>
