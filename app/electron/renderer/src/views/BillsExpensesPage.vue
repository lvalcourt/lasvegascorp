<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-300/75">Bills & Expenses</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">Move receipts into structured spend records.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            This workspace now bridges document intake, category mapping, and shared transactions so bill review turns into a clean business workflow instead of a detached inbox.
          </p>
        </div>
        <div class="flex flex-wrap gap-3">
          <router-link to="/categories" class="rounded-2xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white">Manage Categories</router-link>
          <router-link to="/transactions" class="rounded-2xl bg-rose-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-rose-300">View All Transactions</router-link>
        </div>
      </div>
    </section>

    <section class="mt-6 grid gap-6 xl:grid-cols-[420px_1fr]">
      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-white">{{ editingId ? "Update Bill or Expense" : "Create Bill or Expense" }}</h3>
            <p class="mt-1 text-xs text-slate-400">Shared transaction record with optional receipt linkage.</p>
          </div>
          <span class="text-[11px] uppercase tracking-[0.2em] text-slate-500">{{ sourceDocumentId ? "Receipt-linked" : "Manual" }}</span>
        </div>

        <div v-if="sourceDocumentId && linkedReceiptLabel" class="mt-4 rounded-2xl border border-cyan-400/25 bg-cyan-400/10 p-3 text-xs text-cyan-100">
          Creating from receipt: <span class="font-semibold">{{ linkedReceiptLabel }}</span>
          <button class="ml-2 text-cyan-200 underline underline-offset-2 hover:text-white" @click="clearReceiptSelection">Clear</button>
        </div>

        <form class="mt-4 space-y-3" @submit.prevent="saveBill">
          <select v-model="form.payee_id" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
            <option :value="null">Choose vendor/payee</option>
            <option v-for="row in payees" :key="row.id" :value="row.id">{{ row.name }}</option>
          </select>
          <select v-model="form.company_id" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
            <option :value="null">Choose company</option>
            <option v-for="row in companies" :key="row.id" :value="row.id">{{ row.name }}</option>
          </select>
          <div class="grid gap-3 sm:grid-cols-2">
            <select v-model="form.transaction_type" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
              <option value="bill">Bill</option>
              <option value="expense">Expense</option>
            </select>
            <select v-model="form.status" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
              <option value="open">Open</option>
              <option value="posted">Posted</option>
              <option value="paid">Paid</option>
            </select>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model="form.transaction_date" type="date" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <input v-model="form.due_date" type="date" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model.number="form.amount" type="number" step="0.01" min="0" placeholder="Amount" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <input v-model="form.category" list="category-options" type="text" placeholder="Category" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          </div>
          <datalist id="category-options">
            <option v-for="category in categories" :key="category.id" :value="category.name" />
          </datalist>
          <div class="grid gap-3 sm:grid-cols-2">
            <input v-model="form.reference_number" type="text" placeholder="Reference number" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <input v-model="form.document_type" type="text" placeholder="Document type" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          </div>
          <textarea v-model="form.notes" rows="3" placeholder="Notes" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          <div class="flex flex-wrap gap-2">
            <button class="rounded-md bg-rose-400 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-rose-300" :disabled="saving">
              {{ saving ? "Saving..." : editingId ? "Update Bill / Expense" : sourceDocumentId ? "Create From Receipt" : "Save Bill / Expense" }}
            </button>
            <button
              v-if="editingId || sourceDocumentId"
              type="button"
              class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500"
              @click="resetForm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      <div class="space-y-6">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-white">Receipt Intake</h3>
              <p class="mt-1 text-xs text-slate-400">Upload receipts or bills, then classify them into categories and transactions.</p>
            </div>
            <label class="inline-flex cursor-pointer items-center rounded-md bg-cyan-400 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-cyan-300">
              Upload Receipt
              <input type="file" class="hidden" accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv" @change="onPickReceipt" />
            </label>
          </div>
          <div v-if="selectedReceipt" class="mt-3 text-xs text-slate-300">{{ selectedReceipt.name }}</div>
          <button
            class="mt-3 rounded-md border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-xs font-semibold text-cyan-200 transition hover:border-cyan-300/50 hover:text-cyan-100 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
            :disabled="!selectedReceipt || uploadingReceipt"
            @click="uploadReceipt"
          >
            {{ uploadingReceipt ? "Uploading..." : "Save to Receipt Inbox" }}
          </button>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-white">Open Bills & Expenses</h3>
              <p class="mt-1 text-xs text-slate-400">Shared ledger entries with bill and expense transaction types.</p>
            </div>
            <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadData">Refresh</button>
          </div>
          <div class="mt-4 overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">Vendor</th>
                  <th class="pb-2 pr-3">Type</th>
                  <th class="pb-2 pr-3">Status</th>
                  <th class="pb-2 pr-3">Date</th>
                  <th class="pb-2 pr-3">Due</th>
                  <th class="pb-2 pr-3">Amount</th>
                  <th class="pb-2 pr-3">Category</th>
                  <th class="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in rows" :key="row.id" class="border-t border-slate-800 text-slate-200">
                  <td class="py-2 pr-3">{{ row.payee_name || "" }}</td>
                  <td class="py-2 pr-3">{{ row.transaction_type }}</td>
                  <td class="py-2 pr-3">{{ row.status }}</td>
                  <td class="py-2 pr-3">{{ row.transaction_date || "" }}</td>
                  <td class="py-2 pr-3">{{ row.due_date || "" }}</td>
                  <td class="py-2 pr-3">{{ currency(row.amount) }}</td>
                  <td class="py-2 pr-3">{{ row.category || "" }}</td>
                  <td class="py-2 whitespace-nowrap">
                    <button class="mr-2 text-cyan-300 hover:text-cyan-100" @click="startEdit(row)">Edit</button>
                    <button class="text-rose-300 hover:text-rose-100" @click="removeTransaction(row.id)">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-white">Receipt Review Queue</h3>
              <p class="mt-1 text-xs text-slate-400">Classify uploaded documents by assigning a category, then create or link the matching transaction.</p>
            </div>
          </div>
          <div class="mt-4 overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">File</th>
                  <th class="pb-2 pr-3">Status</th>
                  <th class="pb-2 pr-3">Category</th>
                  <th class="pb-2 pr-3">Linked Transaction</th>
                  <th class="pb-2 pr-3">Uploaded</th>
                  <th class="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in expenseDocuments" :key="row.id" class="border-t border-slate-800 text-slate-200 align-top">
                  <td class="py-3 pr-3">
                    <div class="font-medium text-white">{{ row.filename }}</div>
                    <div class="mt-1 text-[11px] text-slate-400">
                      <span v-if="row.payee_name">{{ row.payee_name }}</span>
                      <span v-if="row.payee_name && row.company_name"> · </span>
                      <span v-if="row.company_name">{{ row.company_name }}</span>
                    </div>
                  </td>
                  <td class="py-3 pr-3">{{ row.status }}</td>
                  <td class="py-3 pr-3">
                    <input
                      v-model="receiptDrafts[row.id].suggested_category"
                      list="category-options"
                      type="text"
                      placeholder="Suggested category"
                      class="w-40 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-[11px]"
                    />
                  </td>
                  <td class="py-3 pr-3">
                    <div v-if="row.linked_transaction_id" class="text-emerald-300">
                      #{{ row.linked_transaction_id }} · {{ row.transaction_type || "transaction" }}
                      <div class="text-[11px] text-slate-400">{{ currency(row.linked_amount || 0) }}</div>
                    </div>
                    <select
                      v-else
                      v-model="receiptDrafts[row.id].transaction_id"
                      class="w-44 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-[11px]"
                    >
                      <option :value="null">Link to existing...</option>
                      <option v-for="option in rows" :key="option.id" :value="option.id">
                        #{{ option.id }} · {{ option.payee_name || "Unassigned" }} · {{ currency(option.amount) }}
                      </option>
                    </select>
                  </td>
                  <td class="py-3 pr-3">{{ row.uploaded_at || "" }}</td>
                  <td class="py-3 whitespace-nowrap">
                    <button class="mr-2 text-slate-300 hover:text-white" @click="openReceipt(row)">Open</button>
                    <button class="mr-2 text-cyan-300 hover:text-cyan-100" @click="startFromReceipt(row)">Create</button>
                    <button
                      class="mr-2 text-emerald-300 hover:text-emerald-100 disabled:text-slate-600"
                      :disabled="!receiptDrafts[row.id].transaction_id || !!row.linked_transaction_id"
                      @click="linkReceipt(row)"
                    >
                      Link
                    </button>
                    <button class="text-amber-300 hover:text-amber-100" @click="markReceiptReviewed(row)">Review</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { authHeaders } from "../auth";

const API_BASE = "http://127.0.0.1:8000";

const rows = ref<any[]>([]);
const payees = ref<any[]>([]);
const companies = ref<any[]>([]);
const categories = ref<any[]>([]);
const expenseDocuments = ref<any[]>([]);
const saving = ref(false);
const uploadingReceipt = ref(false);
const selectedReceipt = ref<File | null>(null);
const editingId = ref<number | null>(null);
const sourceDocumentId = ref<string | null>(null);
const receiptDrafts = reactive<Record<string, { transaction_id: number | null; suggested_category: string }>>({});
const form = reactive<any>({
  payee_id: null,
  company_id: null,
  transaction_type: "bill",
  status: "open",
  transaction_date: "",
  due_date: "",
  amount: 0,
  category: "",
  reference_number: "",
  document_type: "",
  notes: "",
});

const linkedReceiptLabel = computed(() => {
  if (!sourceDocumentId.value) return "";
  return expenseDocuments.value.find((row) => row.id === sourceDocumentId.value)?.filename || "";
});

const ensureReceiptDraft = (row: any) => {
  if (!receiptDrafts[row.id]) {
    receiptDrafts[row.id] = {
      transaction_id: row.linked_transaction_id || null,
      suggested_category: row.suggested_category || "",
    };
  }
};

const loadData = async () => {
  const [billsResponse, payeesResponse, companiesResponse, expenseDocsResponse, categoriesResponse] = await Promise.all([
    fetch(`${API_BASE}/bills`),
    fetch(`${API_BASE}/payments/payees`),
    fetch(`${API_BASE}/companies`),
    fetch(`${API_BASE}/expense-documents`),
    fetch(`${API_BASE}/categories?kind=expense`),
  ]);
  if (billsResponse.ok) rows.value = await billsResponse.json();
  if (payeesResponse.ok) payees.value = await payeesResponse.json();
  if (companiesResponse.ok) companies.value = await companiesResponse.json();
  if (categoriesResponse.ok) categories.value = await categoriesResponse.json();
  if (expenseDocsResponse.ok) {
    expenseDocuments.value = await expenseDocsResponse.json();
    for (const row of expenseDocuments.value) ensureReceiptDraft(row);
  }
};

const saveBill = async () => {
  saving.value = true;
  try {
    const endpoint = editingId.value
      ? `${API_BASE}/transactions/${editingId.value}`
      : sourceDocumentId.value
        ? `${API_BASE}/expense-documents/${sourceDocumentId.value}/create-transaction`
        : `${API_BASE}/bills`;
    const method = editingId.value ? "PUT" : "POST";
    const payload = {
      ...form,
      document_status: sourceDocumentId.value && !editingId.value ? "classified" : undefined,
      document_notes: sourceDocumentId.value ? `Created from receipt ${linkedReceiptLabel.value}.` : undefined,
    };
    const response = await fetch(endpoint, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) return;
    resetForm();
    await loadData();
  } finally {
    saving.value = false;
  }
};

const resetForm = () => {
  editingId.value = null;
  sourceDocumentId.value = null;
  Object.assign(form, {
    payee_id: null,
    company_id: null,
    transaction_type: "bill",
    status: "open",
    transaction_date: "",
    due_date: "",
    amount: 0,
    category: "",
    reference_number: "",
    document_type: "",
    notes: "",
  });
};

const clearReceiptSelection = () => {
  sourceDocumentId.value = null;
};

const startEdit = (row: any) => {
  editingId.value = row.id;
  sourceDocumentId.value = null;
  Object.assign(form, {
    payee_id: payees.value.find((item) => item.name === row.payee_name)?.id ?? null,
    company_id: companies.value.find((item) => item.name === row.company_name)?.id ?? null,
    transaction_type: row.transaction_type,
    status: row.status,
    transaction_date: row.transaction_date || "",
    due_date: row.due_date || "",
    amount: row.amount,
    category: row.category || "",
    reference_number: row.reference_number || "",
    document_type: row.document_type || "",
    notes: row.notes || "",
  });
};

const startFromReceipt = (row: any) => {
  ensureReceiptDraft(row);
  editingId.value = null;
  sourceDocumentId.value = row.id;
  Object.assign(form, {
    payee_id: row.payee_id ?? null,
    company_id: row.company_id ?? null,
    transaction_type: "expense",
    status: "posted",
    transaction_date: "",
    due_date: "",
    amount: Number(row.linked_amount || 0),
    category: receiptDrafts[row.id].suggested_category || row.suggested_category || "",
    reference_number: "",
    document_type: "receipt",
    notes: row.notes || "",
  });
};

const removeTransaction = async (transactionId: number) => {
  const confirmed = window.confirm("Delete this transaction?");
  if (!confirmed) return;
  const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) return;
  if (editingId.value === transactionId) resetForm();
  await loadData();
};

const onPickReceipt = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedReceipt.value = input.files[0];
  }
};

const uploadReceipt = async () => {
  if (!selectedReceipt.value) return;
  uploadingReceipt.value = true;
  try {
    const payload = new FormData();
    payload.append("file", selectedReceipt.value);
    const response = await fetch(`${API_BASE}/expense-documents`, {
      method: "POST",
      body: payload,
      headers: authHeaders(),
    });
    if (!response.ok) return;
    selectedReceipt.value = null;
    await loadData();
  } finally {
    uploadingReceipt.value = false;
  }
};

const linkReceipt = async (row: any) => {
  ensureReceiptDraft(row);
  const draft = receiptDrafts[row.id];
  if (!draft.transaction_id) return;
  const response = await fetch(`${API_BASE}/expense-documents/${row.id}/link-transaction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({
      transaction_id: draft.transaction_id,
      suggested_category: draft.suggested_category || row.suggested_category || "",
      notes: `Linked from receipt queue for ${row.filename}.`,
    }),
  });
  if (!response.ok) return;
  await loadData();
};

const markReceiptReviewed = async (row: any) => {
  ensureReceiptDraft(row);
  const response = await fetch(`${API_BASE}/expense-documents/${row.id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({
      status: row.linked_transaction_id ? "classified" : "reviewed",
      notes: row.notes || "Reviewed from Bills & Expenses workspace.",
      linked_transaction_id: row.linked_transaction_id || null,
      suggested_category: receiptDrafts[row.id].suggested_category || row.suggested_category || "",
      payee_id: row.payee_id || null,
      company_id: row.company_id || null,
    }),
  });
  if (!response.ok) return;
  await loadData();
};

const openReceipt = (row: any) => {
  window.open(`${API_BASE}/documents/expense/${row.id}/download`, "_blank", "noopener,noreferrer");
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

onMounted(loadData);
</script>
