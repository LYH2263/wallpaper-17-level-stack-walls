<script setup>
import { computed } from 'vue'

// 楼层选择器：每层一个名称 + 该层墙面多选；同一面墙只能属于一层。
const props = defineProps({
  walls: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }, // [{ floor: '1F', wall_ids: [1, 2] }]
})
const emit = defineEmits(['update:modelValue'])

const owners = computed(() => {
  const map = {}
  props.modelValue.forEach((f, i) => f.wall_ids.forEach((id) => { (map[id] = map[id] || []).push(i) }))
  return map
})

function emitFloors(floors) { emit('update:modelValue', floors) }
function addFloor() {
  emitFloors([...props.modelValue, { floor: `${props.modelValue.length + 1}F`, wall_ids: [] }])
}
function removeFloor(i) {
  emitFloors(props.modelValue.filter((_, idx) => idx !== i))
}
function renameFloor(i, floor) {
  emitFloors(props.modelValue.map((f, idx) => (idx === i ? { ...f, floor } : f)))
}
function toggleWall(i, wid, checked) {
  emitFloors(props.modelValue.map((f, idx) => {
    if (idx !== i) return f
    const wall_ids = checked ? [...f.wall_ids, wid] : f.wall_ids.filter((id) => id !== wid)
    return { ...f, wall_ids }
  }))
}
function takenByOtherFloor(i, wid) {
  return (owners.value[wid] || []).some((idx) => idx !== i)
}
</script>

<template>
  <div class="floor-picker">
    <div v-for="(f, i) in modelValue" :key="i" class="floor-group">
      <input class="floor-name" :value="f.floor" placeholder="楼层，如 1F"
             @input="renameFloor(i, $event.target.value)" />
      <label v-for="w in walls" :key="w.id" class="wall-chip">
        <input type="checkbox" :checked="f.wall_ids.includes(w.id)"
               :disabled="takenByOtherFloor(i, w.id)"
               @change="toggleWall(i, w.id, $event.target.checked)" />
        {{ w.name }}
      </label>
      <button type="button" @click="removeFloor(i)">删除本层</button>
    </div>
    <button type="button" @click="addFloor">+ 添加楼层</button>
  </div>
</template>
