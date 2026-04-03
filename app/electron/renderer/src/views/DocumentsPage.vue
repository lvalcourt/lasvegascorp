<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/75">Documents</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">One inbox for business uploads.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Review uploaded business documents across payments and operational spreadsheets, then move into the right workflow from one place.
          </p>
        </div>
        <div class="flex gap-3">
          <router-link to="/bills-expenses" class="rounded-2xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white">Review Receipts</router-link>
          <router-link to="/payments" class="rounded-2xl bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300">Open Payments</router-link>
          <router-link to="/imports" class="rounded-2xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white">Open Imports</router-link>
        </div>
      </div>

      <div class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Payment Uploads</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ overview.totals.payment_imports_count }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Spreadsheet Imports</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ overview.totals.spreadsheet_imports_count }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Active Payees</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ overview.totals.current_year_active_payees }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Current Year Spend</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ currency(overview.totals.current_year_payment_total) }}</div>
        </div>
      </div>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-white">Recent Documents</h3>
          <p class="mt-1 text-xs text-slate-400">Recent uploads across payment documents and spreadsheet-based workflows.</p>
        </div>
        <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadData">Refresh</button>
      </div>

      <div class="mt-4 overflow-auto">
        <table class="min-w-full text-left text-xs">
          <thead class="text-slate-400">
            <tr>
              <th class="pb-2 pr-3">File</th>
              <th class="pb-2 pr-3">Type</th>
              <th class="pb-2 pr-3">Rows</th>
              <th class="pb-2 pr-3">Status</th>
              <th class="pb-2 pr-3">Mapped Workflow</th>
              <th class="pb-2 pr-3">Notes</th>
              <th class="pb-2 pr-3">Uploaded</th>
              <th class="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="`${row.document_group}-${row.id}`" class="border-t border-slate-800 text-slate-200">
              <td class="py-2 pr-3">{{ row.filename }}</td>
              <td class="py-2 pr-3">{{ row.document_group }}</td>
              <td class="py-2 pr-3">{{ row.row_count || 0 }}</td>
              <td class="py-2 pr-3">{{ row.status }}</td>
              <td class="py-2 pr-3">
                <div v-if="row.linked_transaction_id" class="text-emerald-300">
                  Transaction #{{ row.linked_transaction_id }}
                </div>
                <div v-else-if="row.suggested_category || row.payee_name || row.company_name" class="text-cyan-200">
                  {{ [row.suggested_category, row.payee_name, row.company_name].filter(Boolean).join(" · ") }}
                </div>
                <div v-else class="text-slate-500">Not mapped yet</div>
              </td>
              <td class="py-2 pr-3">{{ row.notes || "" }}</td>
              <td class="py-2 pr-3">{{ formatDate(row.uploaded_at) }}</td>
              <td class="py-2">
                <button
                  v-if="canOpenDocument(row)"
                  class="text-cyan-300 hover:text-cyan-100"
                  @click="openDocument(row)"
                >
                  Open
                </button>
                <span v-else class="text-slate-500">No file</span>
              </td>
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

const overview = reactive<any>({
  totals: {
    payment_imports_count: 0,
    spreadsheet_imports_count: 0,
    current_year_active_payees: 0,
    current_year_payment_total: 0,
  },
});
const rows = ref<any[]>([]);

const loadData = async () => {
  const [overviewResponse, docsResponse] = await Promise.all([
    fetch(`${API_BASE}/business/overview`),
    fetch(`${API_BASE}/documents`),
  ]);
  if (overviewResponse.ok) {
    const data = await overviewResponse.json();
    overview.totals = data.totals;
  }
  if (docsResponse.ok) {
    rows.value = await docsResponse.json();
  }
};

const canOpenDocument = (row: any) => ["payment", "expense", "generic", "payroll_summary"].includes(String(row.document_group || ""));

const openDocument = (row: any) => {
  if (!canOpenDocument(row)) return;
  window.open(`${API_BASE}/documents/${row.document_group}/${row.id}/download`, "_blank", "noopener,noreferrer");
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

const formatDate = (value: string) => {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

onMounted(loadData);
</script>
