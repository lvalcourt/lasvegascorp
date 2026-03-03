<template>
  <main class="px-8 py-8">
    <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div class="grid gap-3 sm:grid-cols-6">
        <input v-model="filters.search" type="text" placeholder="Search employee/patient/task" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model="filters.import_id" type="text" placeholder="Import ID" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model="filters.classification" type="text" placeholder="Classification" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model="filters.branch" type="text" placeholder="Branch" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model="filters.date_from" type="date" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model="filters.date_to" type="date" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
      </div>

      <div class="mt-3 flex gap-2">
        <button class="rounded-md bg-indigo-500 px-3 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400" @click="loadRecords">Apply Filters</button>
        <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="resetFilters">Reset</button>
      </div>
    </section>

    <section class="mt-6 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h2 class="text-lg font-semibold">Records</h2>
      <div class="mt-3 max-h-[620px] overflow-auto">
        <table class="min-w-full text-left text-xs">
          <thead class="text-slate-400">
            <tr>
              <th class="pb-2 pr-3">Employee</th>
              <th class="pb-2 pr-3">Date</th>
              <th class="pb-2 pr-3">Patient</th>
              <th class="pb-2 pr-3">Task</th>
              <th class="pb-2 pr-3">Class</th>
              <th class="pb-2 pr-3">Rate</th>
              <th class="pb-2 pr-3">Mileage</th>
              <th class="pb-2 pr-3">Surcharge</th>
              <th class="pb-2 pr-3">Branch</th>
              <th class="pb-2">Import</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.id" class="border-t border-slate-800 text-slate-200">
              <td class="py-2 pr-3">{{ row.employee_name }}</td>
              <td class="py-2 pr-3">{{ row.entry_date || "" }}</td>
              <td class="py-2 pr-3">{{ row.patient_name || "" }}</td>
              <td class="py-2 pr-3">{{ row.task || "" }}</td>
              <td class="py-2 pr-3">{{ row.classification }}</td>
              <td class="py-2 pr-3">{{ formatNum(row.rate) }}</td>
              <td class="py-2 pr-3">{{ formatNum(row.mileage) }}</td>
              <td class="py-2 pr-3">{{ formatNum(row.surcharge) }}</td>
              <td class="py-2 pr-3">{{ row.branch || "" }}</td>
              <td class="py-2">{{ row.filename }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

const API_BASE = "http://127.0.0.1:8000";

const filters = reactive({
  search: "",
  import_id: "",
  classification: "",
  branch: "",
  date_from: "",
  date_to: "",
});

const rows = ref<any[]>([]);

const buildQuery = () => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });
  return params.toString();
};

const loadRecords = async () => {
  const query = buildQuery();
  const response = await fetch(`${API_BASE}/records${query ? `?${query}` : ""}`);
  rows.value = await response.json();
};

const resetFilters = async () => {
  filters.search = "";
  filters.import_id = "";
  filters.classification = "";
  filters.branch = "";
  filters.date_from = "";
  filters.date_to = "";
  await loadRecords();
};

const formatNum = (value: number) => Number(value || 0).toFixed(2);

onMounted(async () => {
  await loadRecords();
});
</script>
