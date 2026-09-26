<script setup>
const props = defineProps({
  walls: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

function update(floors) { emit('update:modelValue', floors) }
function addFloor() {
  update([...props.modelValue, { floor: `${props.modelValue.length + 1}F`, wall_ids: [] }])
}
function removeFloor(i) {
  update(props.modelValue.filter((_, idx) => idx !== i))
}
function renameFloor(i, name) {
  update(props.modelValue.map((f, idx) => (idx === i ? { ...f, floor: name } : f)))
}
function toggleWall(i, wid) {
  update(props.modelValue.map((f, idx) => {
    if (idx !== i) return f
    const has = f.wall_ids.includes(wid)
    return { ...f, wall_ids: has ? f.wall_ids.filter(id => id !== wid) : [...f.wall_ids, wid] }
  }))
}
function usedElsewhere(i, wid) {
  return props.modelValue.some((f, idx) => idx !== i && f.wall_ids.includes(wid))
}
</script>
<template>
  <div class="floor-picker">
    <div v-for="(f, i) in modelValue" :key="i" class="floor-row">
      <input class="floor-name" :value="f.floor" placeholder="楼层" @input="renameFloor(i, $event.target.value)" />
      <label v-for="w in walls" :key="w.id" class="wall-check">
        <input type="checkbox" :checked="f.wall_ids.includes(w.id)" :disabled="usedElsewhere(i, w.id)" @change="toggleWall(i, w.id)" />
        {{ w.name }}
      </label>
      <button type="button" @click="removeFloor(i)">移除本层</button>
    </div>
    <button type="button" @click="addFloor">添加楼层</button>
  </div>
</template>
