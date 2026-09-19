<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => {
  items.value = (await getJSON('/api/history')).items.map(h => {
    let input = {}, result = {}
    try { input = JSON.parse(h.input_json); result = JSON.parse(h.result_json) } catch (e) { /* legacy rows */ }
    return { ...h, input, result }
  })
})
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr><th>#</th><th>时间</th><th>区间</th><th>应付</th><th>一日通</th></tr>
      <tr v-for="h in items" :key="h.id">
        <td>#{{ h.id }}</td><td>{{ h.created_at }}</td>
        <template v-if="h.result.reachable">
          <td>{{ h.input.start }} → {{ h.input.end }}</td>
          <td>¥{{ h.result.fare }}</td>
          <td>
            <span v-if="h.result.day_pass && h.result.day_pass.capped">触顶（原价 ¥{{ h.result.original_fare }}）</span>
            <span v-else-if="h.result.day_pass && h.result.day_pass.applied">未触顶</span>
            <span v-else class="muted">—</span>
          </td>
        </template>
        <td v-else colspan="3" class="muted">不可达</td>
      </tr>
    </table>
  </div>
</template>
