<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-300/75">Vendors</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">Manage service providers and business payees.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            This view generalizes payees into a vendor directory for small businesses. It connects payment history, tax IDs, and profile maintenance in one route.
          </p>
        </div>
        <router-link to="/payment-profiles" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300">Open Vendor Profiles</router-link>
      </div>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div class="flex items-center justify-between">
        <input v-model="search" type="text" placeholder="Search vendor, tax ID, or city" class="w-full max-w-sm rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
        <div class="flex gap-2">
          <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="exportVendorsCsv">Export CSV</button>
          <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadVendors">Refresh</button>
        </div>
      </div>

      <div class="mt-4 overflow-auto">
        <table class="min-w-full text-left text-xs">
          <thead class="text-slate-400">
            <tr>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('name')">Vendor</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('tax_id')">Tax ID</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('payee_type')">Type</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('city')">Location</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('payments_count')">Payments</button></th>
              <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleSort('amount_total')">Total Paid</button></th>
              <th class="pb-2">Contact</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in sortedRows" :key="row.id" class="border-t border-slate-800 text-slate-200">
              <td class="py-2 pr-3">{{ row.name }}</td>
              <td class="py-2 pr-3">{{ row.tax_id || "" }}</td>
              <td class="py-2 pr-3">{{ row.payee_type || "" }}</td>
              <td class="py-2 pr-3">{{ [row.city, row.state].filter(Boolean).join(', ') }}</td>
              <td class="py-2 pr-3">{{ row.payments_count || 0 }}</td>
              <td class="py-2 pr-3">{{ currency(row.amount_total) }}</td>
              <td class="py-2">{{ row.email || row.phone || "" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { downloadCsv } from "../csv";
import { loadStoredState, saveStoredState } from "../storage";
import { sortRows, type SortDirection } from "../table";

const API_BASE = "http://127.0.0.1:8000";
const STORAGE_KEY = "trakinpr-vendors-page";
const pageState = loadStoredState(STORAGE_KEY, {
  search: "",
  sortKey: "name",
  sortDirection: "asc" as SortDirection,
});

const search = ref(pageState.search);
const rows = ref<any[]>([]);
const sortKey = ref(pageState.sortKey);
const sortDirection = ref<SortDirection>(pageState.sortDirection);
const sortedRows = computed(() => sortRows(rows.value, sortKey.value, sortDirection.value));

const loadVendors = async () => {
  const params = new URLSearchParams();
  if (search.value) params.append("search", search.value);
  const response = await fetch(`${API_BASE}/vendors?${params.toString()}`);
  if (!response.ok) return;
  rows.value = await response.json();
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

const exportVendorsCsv = () => {
  downloadCsv(
    "trakinpr-vendors.csv",
    ["Vendor", "Tax ID", "Type", "Location", "Payments", "Total Paid", "Contact"],
    sortedRows.value.map((row) => [
      row.name || "",
      row.tax_id || "",
      row.payee_type || "",
      [row.city, row.state].filter(Boolean).join(", "),
      row.payments_count || 0,
      Number(row.amount_total || 0).toFixed(2),
      row.email || row.phone || "",
    ]),
  );
};

watch(search, () => {
  loadVendors();
});

watch([search, sortKey, sortDirection], () => {
  saveStoredState(STORAGE_KEY, {
    search: search.value,
    sortKey: sortKey.value,
    sortDirection: sortDirection.value,
  });
});

onMounted(loadVendors);
</script>
