<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'
const s = ref({})
const day = ref('')
const cap = ref(10)
const enabled = ref(false)
const msg = ref('')
const err = ref('')
onMounted(async () => {
  s.value = await getJSON('/api/settings')
  const cur = await getJSON('/api/day-pass')
  if (cur) { day.value = cur.day || ''; cap.value = cur.cap ?? 10; enabled.value = !!cur.enabled }
})
const save = async () => {
  msg.value = ''; err.value = ''
  try {
    const r = await putJSON('/api/day-pass', { day: day.value, cap: Number(cap.value), enabled: enabled.value })
    msg.value = `已保存：${r.day} 封顶 ¥${r.cap} · ${r.enabled ? '启用' : '停用'}`
  } catch (e) {
    err.value = '保存失败：封顶须为正数，日期需为 YYYY-MM-DD'
  }
}
</script>
<template>
  <div class="page"><h1>设置</h1>
    <div class="panel">
      <h2>一日通</h2>
      <p><label>自然日 <input type="date" v-model="day"></label></p>
      <p><label>封顶金额 <input type="number" min="0.01" step="0.01" v-model="cap"></label></p>
      <p><label><input type="checkbox" v-model="enabled"> 启用一日通</label></p>
      <button @click="save">保存</button>
      <span v-if="msg" class="muted"> {{ msg }}</span>
      <span v-if="err" class="err"> {{ err }}</span>
    </div>
    <div class="panel"><h2>系统</h2><pre>{{ s }}</pre></div>
  </div>
</template>
