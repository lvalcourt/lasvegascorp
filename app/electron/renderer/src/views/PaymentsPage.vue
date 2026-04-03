<template>
  <main class="px-8 py-8">
    <div class="grid gap-6 xl:grid-cols-[420px_1fr]">
      <section class="space-y-6">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-white">Payments Workspace</h2>
              <p class="mt-1 text-xs text-slate-400">Upload payment backups and keep a searchable ledger for future 480 preparation.</p>
              <p class="mt-2 text-[11px] leading-5 text-slate-500">Current focus: payments for services rendered that can feed Form 480.6SP preparation.</p>
            </div>
            <span class="rounded-full border border-slate-800 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300">
              {{ authState.role }}
            </span>
          </div>

          <div v-if="canManagePayments" class="mt-5 space-y-4">
            <div class="flex gap-2">
              <router-link to="/payment-profiles" class="rounded-md border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition hover:border-cyan-300/50 hover:text-cyan-100">
                Manage Profiles
              </router-link>
              <router-link to="/form-480-prep" class="rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs font-semibold text-amber-200 transition hover:border-amber-300/50 hover:text-amber-100">
                Open 480.6SP Prep
              </router-link>
            </div>
            <div>
              <label class="inline-flex cursor-pointer items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400">
                Choose Payment File
                <input type="file" class="hidden" accept=".xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg" @change="onPickFile" />
              </label>
              <div v-if="selectedFile" class="mt-2 text-xs text-slate-300">{{ selectedFile.name }}</div>
            </div>

            <button
              class="rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
              :disabled="!selectedFile || uploading"
              @click="uploadPaymentFile"
            >
              {{ uploading ? "Uploading..." : "Upload Payment File" }}
            </button>
            <p v-if="uploadMessage" class="text-xs text-emerald-300">{{ uploadMessage }}</p>
            <p v-if="uploadError" class="text-xs text-rose-300">{{ uploadError }}</p>
          </div>

          <div v-else class="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-xs text-slate-400">
            Viewer role can review payment history and 480 totals, but uploads and edits require operator access.
          </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-white">Quick Manual Entry</h3>
            <span class="text-[11px] text-slate-500">For payments not yet in a spreadsheet</span>
          </div>

          <form class="mt-4 space-y-3" @submit.prevent="createManualRecord">
            <input v-model="manualForm.payee_name" type="text" placeholder="Payee name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="manualForm.payment_date" type="date" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
              <input v-model.number="manualForm.amount" type="number" step="0.01" min="0" placeholder="Amount" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="manualForm.tax_id" type="text" placeholder="Tax ID" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
              <input v-model="manualForm.reference_number" type="text" placeholder="Reference number" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="manualForm.category" type="text" placeholder="Category" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
              <input v-model="manualForm.document_type" type="text" placeholder="Document type" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
            </div>
            <textarea v-model="manualForm.notes" rows="3" placeholder="Notes" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canManagePayments" />
            <button
              type="submit"
              class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500 disabled:cursor-not-allowed disabled:text-slate-500"
              :disabled="savingManual || !canManagePayments"
            >
              {{ savingManual ? "Saving..." : "Save Manual Payment" }}
            </button>
          </form>
        </div>
      </section>

      <section class="space-y-6">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="grid gap-3 sm:grid-cols-3">
            <input v-model="filters.search" type="text" placeholder="Search payee, category, reference" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <input v-model.number="filters.tax_year" type="number" min="2000" step="1" placeholder="Tax year" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <label class="inline-flex items-center gap-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
              <input v-model="filters.include_history" type="checkbox" />
              Include history
            </label>
          </div>
          <div class="mt-3 flex gap-2">
            <button class="rounded-md bg-indigo-500 px-3 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400" @click="loadRecords">Apply Filters</button>
            <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="resetFilters">Reset</button>
            <button class="rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:border-slate-500" @click="exportPaymentRecordsCsv">Export CSV</button>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-white">Payment Imports</h3>
            <div class="flex gap-2">
              <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="exportPaymentImportsCsv">Export CSV</button>
              <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadPaymentImports">Refresh</button>
            </div>
          </div>
          <div class="mt-4 overflow-x-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleImportsSort('filename')">File</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleImportsSort('status')">Status</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleImportsSort('row_count')">Rows</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleImportsSort('uploaded_at')">Uploaded</button></th>
                  <th class="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in sortedPaymentImports" :key="item.id" class="border-t border-slate-800 text-slate-200">
                  <td class="py-2 pr-3">{{ item.filename }}</td>
                  <td class="py-2 pr-3">{{ item.status }}</td>
                  <td class="py-2 pr-3">{{ item.row_count }}</td>
                  <td class="py-2 pr-3">{{ formatDate(item.uploaded_at) }}</td>
                  <td class="py-2"><button class="text-cyan-300 hover:text-cyan-100" @click="openPaymentImportFile(item)">Open</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-white">Payment Records</h3>
            <router-link to="/form-480-prep" class="rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-1.5 text-xs font-semibold text-amber-200 transition hover:border-amber-300/50 hover:text-amber-100">
              Open 480.6SP Prep
            </router-link>
          </div>
          <div class="mt-4 max-h-[540px] overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('payee_name')">Payee</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('payment_date')">Date</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('amount')">Amount</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('category')">Category</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('tax_id')">Tax ID</button></th>
                  <th class="pb-2 pr-3"><button class="hover:text-white" @click="toggleRecordsSort('reference_number')">Reference</button></th>
                  <th class="pb-2"><button class="hover:text-white" @click="toggleRecordsSort('filename')">File</button></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in sortedPaymentRows" :key="row.id" class="border-t border-slate-800 text-slate-200">
                  <td class="py-2 pr-3">{{ row.payee_name }}</td>
                  <td class="py-2 pr-3">{{ row.payment_date || "" }}</td>
                  <td class="py-2 pr-3">{{ currency(row.amount) }}</td>
                  <td class="py-2 pr-3">{{ row.category || "" }}</td>
                  <td class="py-2 pr-3">{{ row.tax_id || "" }}</td>
                  <td class="py-2 pr-3">{{ row.reference_number || "" }}</td>
                  <td class="py-2">{{ row.filename || "Manual Entry" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { authHeaders, authState } from "../auth";
import { downloadCsv } from "../csv";
import { loadStoredState, saveStoredState } from "../storage";
import { sortRows, type SortDirection } from "../table";

const API_BASE = "http://127.0.0.1:8000";
const STORAGE_KEY = "trakinpr-payments-page";
const pageState = loadStoredState(STORAGE_KEY, {
  search: "",
  tax_year: new Date().getFullYear(),
  include_history: false,
  importsSortKey: "uploaded_at",
  importsSortDirection: "desc" as SortDirection,
  recordsSortKey: "payment_date",
  recordsSortDirection: "desc" as SortDirection,
});

const canManagePayments = computed(() => authState.role === "admin" || authState.role === "operator");
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const savingManual = ref(false);
const uploadMessage = ref("");
const uploadError = ref("");
const paymentImports = ref<any[]>([]);
const paymentRows = ref<any[]>([]);
const importsSortKey = ref(pageState.importsSortKey);
const importsSortDirection = ref<SortDirection>(pageState.importsSortDirection);
const recordsSortKey = ref(pageState.recordsSortKey);
const recordsSortDirection = ref<SortDirection>(pageState.recordsSortDirection);

const filters = reactive({
  search: pageState.search,
  tax_year: pageState.tax_year,
  include_history: pageState.include_history,
});
const sortedPaymentImports = computed(() => sortRows(paymentImports.value, importsSortKey.value, importsSortDirection.value));
const sortedPaymentRows = computed(() => sortRows(paymentRows.value, recordsSortKey.value, recordsSortDirection.value));

const manualForm = reactive({
  payee_name: "",
  payment_date: "",
  amount: 0,
  category: "",
  document_type: "",
  reference_number: "",
  tax_id: "",
  notes: "",
});

const onPickFile = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0];
  }
};

const uploadPaymentFile = async () => {
  if (!selectedFile.value) return;
  uploadError.value = "";
  uploadMessage.value = "";
  uploading.value = true;
  const payload = new FormData();
  payload.append("file", selectedFile.value);
  try {
    const response = await fetch(`${API_BASE}/payments/imports`, {
      method: "POST",
      body: payload,
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      uploadError.value = data.detail || "Upload failed.";
      return;
    }
    uploadMessage.value = `${data.records_created} records created for ${data.payees_identified} payees.`;
    selectedFile.value = null;
    await Promise.all([loadPaymentImports(), loadRecords()]);
  } catch {
    uploadError.value = "Failed to reach backend.";
  } finally {
    uploading.value = false;
  }
};

const createManualRecord = async () => {
  if (!canManagePayments.value) return;
  savingManual.value = true;
  uploadError.value = "";
  uploadMessage.value = "";
  try {
    const response = await fetch(`${API_BASE}/payments/records`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(manualForm),
    });
    const data = await response.json();
    if (!response.ok) {
      uploadError.value = data.detail || "Failed to save manual payment.";
      return;
    }
    uploadMessage.value = `Manual payment saved for ${data.payee_name}.`;
    Object.assign(manualForm, {
      payee_name: "",
      payment_date: "",
      amount: 0,
      category: "",
      document_type: "",
      reference_number: "",
      tax_id: "",
      notes: "",
    });
    await Promise.all([loadPaymentImports(), loadRecords()]);
  } catch {
    uploadError.value = "Failed to reach backend.";
  } finally {
    savingManual.value = false;
  }
};

const loadPaymentImports = async () => {
  const response = await fetch(`${API_BASE}/payments/imports`);
  paymentImports.value = await response.json();
};

const loadRecords = async () => {
  const params = new URLSearchParams();
  if (filters.search) params.append("search", filters.search);
  if (filters.tax_year) params.append("tax_year", String(filters.tax_year));
  if (filters.include_history) params.append("include_history", "true");
  const response = await fetch(`${API_BASE}/payments/records?${params.toString()}`);
  paymentRows.value = await response.json();
};

const resetFilters = async () => {
  filters.search = "";
  filters.tax_year = new Date().getFullYear();
  filters.include_history = false;
  await loadRecords();
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

const exportPaymentImportsCsv = () => {
  downloadCsv(
    "trakinpr-payment-imports.csv",
    ["File", "Status", "Rows", "Uploaded"],
    sortedPaymentImports.value.map((item) => [item.filename, item.status, item.row_count, item.uploaded_at]),
  );
};

const exportPaymentRecordsCsv = () => {
  downloadCsv(
    "trakinpr-payment-records.csv",
    ["Payee", "Date", "Amount", "Category", "Tax ID", "Reference", "File"],
    sortedPaymentRows.value.map((row) => [
      row.payee_name || "",
      row.payment_date || "",
      Number(row.amount || 0).toFixed(2),
      row.category || "",
      row.tax_id || "",
      row.reference_number || "",
      row.filename || "Manual Entry",
    ]),
  );
};

const toggleImportsSort = (key: string) => {
  if (importsSortKey.value === key) {
    importsSortDirection.value = importsSortDirection.value === "asc" ? "desc" : "asc";
    return;
  }
  importsSortKey.value = key;
  importsSortDirection.value = "asc";
};

const toggleRecordsSort = (key: string) => {
  if (recordsSortKey.value === key) {
    recordsSortDirection.value = recordsSortDirection.value === "asc" ? "desc" : "asc";
    return;
  }
  recordsSortKey.value = key;
  recordsSortDirection.value = "asc";
};

const openPaymentImportFile = (item: any) => {
  window.open(`${API_BASE}/documents/payment/${item.id}/download`, "_blank", "noopener,noreferrer");
};

watch(filters, () => {
  saveStoredState(STORAGE_KEY, {
    ...filters,
    importsSortKey: importsSortKey.value,
    importsSortDirection: importsSortDirection.value,
    recordsSortKey: recordsSortKey.value,
    recordsSortDirection: recordsSortDirection.value,
  });
}, { deep: true });

watch([importsSortKey, importsSortDirection, recordsSortKey, recordsSortDirection], () => {
  saveStoredState(STORAGE_KEY, {
    ...filters,
    importsSortKey: importsSortKey.value,
    importsSortDirection: importsSortDirection.value,
    recordsSortKey: recordsSortKey.value,
    recordsSortDirection: recordsSortDirection.value,
  });
});

onMounted(async () => {
  await Promise.all([loadPaymentImports(), loadRecords()]);
});
</script>
