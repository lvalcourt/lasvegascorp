<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/75">Transactions</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">Track outgoing business activity in one table.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            This workspace turns payment records into a more general transaction view so small businesses can search, review, and reconcile spend.
          </p>
        </div>
        <router-link to="/payments" class="rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300">Add or Review Payments</router-link>
      </div>

      <div class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Transactions</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ summary.rows_count }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Visible Total</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ currency(summary.amount_total) }}</div>
        </div>
      </div>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div class="grid gap-3 sm:grid-cols-3">
        <input v-model="filters.search" type="text" placeholder="Search payee, category, reference" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <input v-model.number="filters.tax_year" type="number" min="2000" step="1" placeholder="Tax year" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <label class="inline-flex items-center gap-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
          <input v-model="filters.include_history" type="checkbox" />
          Include history
        </label>
      </div>
      <div class="mt-3 flex gap-2">
        <button class="rounded-md bg-indigo-500 px-3 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400" @click="loadTransactions">Apply Filters</button>
        <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="resetFilters">Reset</button>
        <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="exportTransactionsCsv">Export CSV</button>
      </div>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div class="overflow-auto">
        <table class="min-w-full text-left text-xs">
          <thead class="text-slate-400">
            <tr>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('payee_name')">Payee</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('payment_date')">Date</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('amount')">Amount</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('category')">Category</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('document_type')">Document Type</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('reference_number')">Reference</button></th>
              <th class="pb-2"><button class="hover:text-white" @click="toggleSort('filename')">Source</button></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in sortedRows" :key="row.id" class="border-t border-slate-800 text-slate-200">
              <td class="py-2 pr-3">{{ row.payee_name }}</td>
              <td class="py-2 pr-3">{{ row.payment_date || "" }}</td>
              <td class="py-2 pr-3">{{ currency(row.amount) }}</td>
              <td class="py-2 pr-3">{{ row.category || "" }}</td>
              <td class="py-2 pr-3">{{ row.document_type || "" }}</td>
              <td class="py-2 pr-3">{{ row.reference_number || "" }}</td>
              <td class="py-2">{{ row.filename || "Manual Entry" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { downloadCsv } from "../csv";
import { loadStoredState, saveStoredState } from "../storage";
import { sortRows, type SortDirection } from "../table";

const API_BASE = "http://127.0.0.1:8000";
const STORAGE_KEY = "trakinpr-transactions-page";
const pageState = loadStoredState(STORAGE_KEY, {
  search: "",
  tax_year: new Date().getFullYear(),
  include_history: false,
  sortKey: "payment_date",
  sortDirection: "desc" as SortDirection,
});

const filters = reactive({
  search: pageState.search,
  tax_year: pageState.tax_year,
  include_history: pageState.include_history,
});
const rows = ref<any[]>([]);
const sortKey = ref(pageState.sortKey);
const sortDirection = ref<SortDirection>(pageState.sortDirection);
const sortedRows = computed(() => sortRows(rows.value, sortKey.value, sortDirection.value));
const summary = reactive({
  rows_count: 0,
  amount_total: 0,
});

const loadTransactions = async () => {
  const params = new URLSearchParams();
  if (filters.search) params.append("search", filters.search);
  if (filters.tax_year) params.append("tax_year", String(filters.tax_year));
  if (filters.include_history) params.append("include_history", "true");
  const response = await fetch(`${API_BASE}/transactions?${params.toString()}`);
  if (!response.ok) return;
  const data = await response.json();
  rows.value = data.rows || [];
  Object.assign(summary, data.summary || { rows_count: 0, amount_total: 0 });
};

const resetFilters = async () => {
  filters.search = "";
  filters.tax_year = new Date().getFullYear();
  filters.include_history = false;
  await loadTransactions();
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

const toggleSort = (key: string) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === "asc" ? "desc" : "asc";
    return;
  }
  sortKey.value = key;
  sortDirection.value = "asc";
};

const exportTransactionsCsv = () => {
  downloadCsv(
    "trakinpr-transactions.csv",
    ["Payee", "Date", "Amount", "Category", "Document Type", "Reference", "Source"],
    sortedRows.value.map((row) => [
      row.payee_name || "",
      row.payment_date || "",
      Number(row.amount || 0).toFixed(2),
      row.category || "",
      row.document_type || "",
      row.reference_number || "",
      row.filename || "Manual Entry",
    ]),
  );
};

watch(filters, () => {
  saveStoredState(STORAGE_KEY, {
    ...filters,
    sortKey: sortKey.value,
    sortDirection: sortDirection.value,
  });
}, { deep: true });

watch([sortKey, sortDirection], () => {
  saveStoredState(STORAGE_KEY, {
    ...filters,
    sortKey: sortKey.value,
    sortDirection: sortDirection.value,
  });
});

onMounted(loadTransactions);
</script>
