<template>
  <main class="px-8 py-8">
    <div class="grid gap-6 lg:grid-cols-[1fr_1fr]">
      <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold">Employees</h2>
          <input
            v-model="search"
            type="text"
            placeholder="Search by first name, last name, or partial words"
            class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs"
            @keyup.enter="loadEmployees"
          />
          <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="loadEmployees">
            Search
          </button>
        </div>
        <div class="mt-3">
          <label class="text-xs text-slate-400">Mileage Multiplier</label>
          <input
            v-model.number="mileagePreference"
            type="number"
            step="0.01"
            min="0"
            class="mt-1 w-44 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs"
          />
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full text-left text-xs">
            <thead class="text-slate-400">
              <tr>
                <th class="pb-2 pr-4">Name</th>
                <th class="pb-2 pr-4">Rows</th>
                <th class="pb-2 pr-4">Rate</th>
                <th class="pb-2 pr-4">Mileage</th>
                <th class="pb-2 pr-4">Mileage x Multiplier</th>
                <th class="pb-2 pr-4">Surcharge</th>
                <th class="pb-2">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="employee in employees"
                :key="employee.id"
                class="cursor-pointer border-t border-slate-800 text-slate-200 hover:bg-slate-800/40"
                @click="selectEmployee(employee.id)"
              >
                <td class="py-2 pr-4">{{ employee.name }}</td>
                <td class="py-2 pr-4">{{ employee.rows_count }}</td>
                <td class="py-2 pr-4">{{ formatNum(employee.rate_total) }}</td>
                <td class="py-2 pr-4">{{ formatNum(employee.mileage_total) }}</td>
                <td class="py-2 pr-4">{{ formatNum(adjustMileage(employee.mileage_total)) }}</td>
                <td class="py-2 pr-4">{{ formatNum(employee.surcharge_total) }}</td>
                <td class="py-2">{{ formatNum(employee.amount_total) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t border-slate-700 text-slate-100">
                <td class="py-2 pr-4 font-semibold">Total</td>
                <td class="py-2 pr-4 font-semibold">{{ employeesTotals.rows_count }}</td>
                <td class="py-2 pr-4 font-semibold">{{ formatNum(employeesTotals.rate_total) }}</td>
                <td class="py-2 pr-4 font-semibold">{{ formatNum(employeesTotals.mileage_total) }}</td>
                <td class="py-2 pr-4 font-semibold">{{ formatNum(adjustMileage(employeesTotals.mileage_total)) }}</td>
                <td class="py-2 pr-4 font-semibold">{{ formatNum(employeesTotals.surcharge_total) }}</td>
                <td class="py-2 font-semibold">{{ formatNum(employeesTotals.amount_total) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-start justify-between">
          <h2 class="text-lg font-semibold">Employee Entries</h2>
          <div v-if="selectedEmployee && sourceSummary" class="text-right text-[11px] text-slate-400">
            <div><span class="text-slate-500">File:</span> {{ sourceSummary.filename }}</div>
            <div><span class="text-slate-500">Loaded:</span> {{ sourceSummary.loaded_at }}</div>
          </div>
        </div>
        <p v-if="!selectedEmployee" class="mt-3 text-xs text-slate-400">Select an employee to view rows.</p>

        <div v-if="selectedEmployee" class="mt-3 text-xs text-slate-300">
          <div class="mb-3">{{ selectedEmployee.name }}</div>
          <div class="max-h-[520px] overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">Date</th>
                  <th class="pb-2 pr-3">Patient Name</th>
                  <th class="pb-2 pr-3">Task</th>
                  <th class="pb-2 pr-3">Class</th>
                  <th class="pb-2 pr-3">Rate</th>
                  <th class="pb-2 pr-3">Mileage</th>
                  <th class="pb-2 pr-3">Mileage x Multiplier</th>
                  <th class="pb-2 pr-3">Surcharge</th>
                  <th class="pb-2">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in entries" :key="entry.id" class="border-t border-slate-800 text-slate-200">
                  <td class="py-2 pr-3">{{ entry.entry_date || "" }}</td>
                  <td class="py-2 pr-3">{{ entry.patient_name || "" }}</td>
                  <td class="py-2 pr-3">{{ entry.task }}</td>
                  <td class="py-2 pr-3">{{ entry.classification }}</td>
                  <td class="py-2 pr-3">{{ formatNum(entry.rate) }}</td>
                  <td class="py-2 pr-3">{{ formatNum(entry.mileage) }}</td>
                  <td class="py-2 pr-3">{{ formatNum(adjustMileage(entry.mileage)) }}</td>
                  <td class="py-2 pr-3">{{ formatNum(entry.surcharge) }}</td>
                  <td class="py-2">{{ formatNum(entry.amount) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="border-t border-slate-700 text-slate-100">
                  <td class="py-2 pr-3 font-semibold">Total</td>
                  <td class="py-2 pr-3"></td>
                  <td class="py-2 pr-3"></td>
                  <td class="py-2 pr-3"></td>
                  <td class="py-2 pr-3 font-semibold">{{ formatNum(entriesTotals.rate_total) }}</td>
                  <td class="py-2 pr-3 font-semibold">{{ formatNum(entriesTotals.mileage_total) }}</td>
                  <td class="py-2 pr-3 font-semibold">{{ formatNum(adjustMileage(entriesTotals.mileage_total)) }}</td>
                  <td class="py-2 pr-3 font-semibold">{{ formatNum(entriesTotals.surcharge_total) }}</td>
                  <td class="py-2 font-semibold">{{ formatNum(entriesTotals.amount_total) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { useMileagePreference } from "../preferences";

const API_BASE = "http://127.0.0.1:8000";

const search = ref("");
const mileagePreference = useMileagePreference();
const employees = ref<any[]>([]);
const selectedEmployee = ref<any>(null);
const entries = ref<any[]>([]);
let searchDebounce: ReturnType<typeof setTimeout> | null = null;

const loadEmployees = async () => {
  const response = await fetch(`${API_BASE}/employees?search=${encodeURIComponent(search.value)}`);
  employees.value = await response.json();
};

const selectEmployee = async (employeeId: number) => {
  const response = await fetch(`${API_BASE}/employees/${employeeId}/entries`);
  if (!response.ok) return;
  const data = await response.json();
  selectedEmployee.value = data.employee;
  entries.value = data.entries;
};

const formatNum = (value: number) => Number(value || 0).toFixed(2);
const adjustMileage = (value: number) => Number(value || 0) * Number(mileagePreference.value || 0);

const employeesTotals = computed(() => {
  return employees.value.reduce(
    (acc, row) => {
      acc.rows_count += Number(row.rows_count || 0);
      acc.rate_total += Number(row.rate_total || 0);
      acc.mileage_total += Number(row.mileage_total || 0);
      acc.surcharge_total += Number(row.surcharge_total || 0);
      acc.amount_total += Number(row.amount_total || 0);
      return acc;
    },
    { rows_count: 0, rate_total: 0, mileage_total: 0, surcharge_total: 0, amount_total: 0 },
  );
});

const entriesTotals = computed(() => {
  return entries.value.reduce(
    (acc, row) => {
      acc.rate_total += Number(row.rate || 0);
      acc.mileage_total += Number(row.mileage || 0);
      acc.surcharge_total += Number(row.surcharge || 0);
      acc.amount_total += Number(row.amount || 0);
      return acc;
    },
    { rate_total: 0, mileage_total: 0, surcharge_total: 0, amount_total: 0 },
  );
});

const sourceSummary = computed(() => {
  if (!entries.value.length) return null;
  const filenames = Array.from(new Set(entries.value.map((e) => e.filename).filter(Boolean)));
  const uploadedValues = entries.value
    .map((e) => e.uploaded_at)
    .filter((v) => !!v)
    .map((v) => new Date(v as string).getTime())
    .filter((v) => !Number.isNaN(v));
  const latest = uploadedValues.length ? new Date(Math.max(...uploadedValues)).toLocaleString() : "N/A";
  return {
    filename: filenames.length === 1 ? filenames[0] : `Multiple (${filenames.length})`,
    loaded_at: latest,
  };
});

watch(search, () => {
  if (searchDebounce) clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    loadEmployees();
  }, 250);
});

onMounted(async () => {
  await loadEmployees();
});
</script>
