<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-violet-300/75">Categories</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">Build category mapping that the workflow can reuse.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Categories now support receipt review, bills and expenses, and the shared transaction ledger. Keeping them in one place makes route transitions feel consistent across the app.
          </p>
        </div>
        <router-link to="/bills-expenses" class="rounded-2xl bg-violet-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-violet-300">Back to Bills & Expenses</router-link>
      </div>
    </section>

    <section class="mt-6 grid gap-6 xl:grid-cols-[380px_1fr]">
      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-white">{{ editingId ? "Update Category" : "Create Category" }}</h3>
          <span class="text-[11px] uppercase tracking-[0.2em] text-slate-500">Reusable mapping</span>
        </div>
        <form class="mt-4 space-y-3" @submit.prevent="saveCategory">
          <input v-model="form.name" type="text" placeholder="Category name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          <div class="grid gap-3 sm:grid-cols-2">
            <select v-model="form.kind" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
              <option value="expense">Expense</option>
              <option value="income">Income</option>
              <option value="payroll">Payroll</option>
            </select>
            <input v-model="form.color_token" type="text" placeholder="Color token" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          </div>
          <textarea v-model="form.description" rows="4" placeholder="Description" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
          <label class="inline-flex items-center gap-2 rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
            <input v-model="form.is_default" type="checkbox" />
            Set as default for this kind
          </label>
          <div class="flex flex-wrap gap-2">
            <button class="rounded-md bg-violet-400 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-violet-300" :disabled="saving">
              {{ saving ? "Saving..." : editingId ? "Update Category" : "Save Category" }}
            </button>
            <button
              v-if="editingId"
              type="button"
              class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500"
              @click="resetForm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-white">Category Library</h3>
            <p class="mt-1 text-xs text-slate-400">Used by receipt review and transaction entry.</p>
          </div>
          <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadCategories">Refresh</button>
        </div>

        <div class="mt-4 overflow-auto">
          <table class="min-w-full text-left text-xs">
            <thead class="text-slate-400">
              <tr>
                <th class="pb-2 pr-3">Name</th>
                <th class="pb-2 pr-3">Kind</th>
                <th class="pb-2 pr-3">Default</th>
                <th class="pb-2 pr-3">Description</th>
                <th class="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.id" class="border-t border-slate-800 text-slate-200">
                <td class="py-2 pr-3">{{ row.name }}</td>
                <td class="py-2 pr-3">{{ row.kind }}</td>
                <td class="py-2 pr-3">{{ row.is_default ? "Yes" : "No" }}</td>
                <td class="py-2 pr-3">{{ row.description || "" }}</td>
                <td class="py-2 whitespace-nowrap">
                  <button class="mr-2 text-cyan-300 hover:text-cyan-100" @click="startEdit(row)">Edit</button>
                  <button class="text-rose-300 hover:text-rose-100" @click="removeCategory(row)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { authHeaders } from "../auth";

const API_BASE = "http://127.0.0.1:8000";

const rows = ref<any[]>([]);
const saving = ref(false);
const editingId = ref<number | null>(null);
const form = reactive({
  name: "",
  kind: "expense",
  description: "",
  color_token: "",
  is_default: false,
});

const loadCategories = async () => {
  const response = await fetch(`${API_BASE}/categories`);
  if (!response.ok) return;
  rows.value = await response.json();
};

const saveCategory = async () => {
  saving.value = true;
  try {
    const response = await fetch(editingId.value ? `${API_BASE}/categories/${editingId.value}` : `${API_BASE}/categories`, {
      method: editingId.value ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(form),
    });
    if (!response.ok) return;
    resetForm();
    await loadCategories();
  } finally {
    saving.value = false;
  }
};

const startEdit = (row: any) => {
  editingId.value = row.id;
  form.name = row.name || "";
  form.kind = row.kind || "expense";
  form.description = row.description || "";
  form.color_token = row.color_token || "";
  form.is_default = Boolean(row.is_default);
};

const resetForm = () => {
  editingId.value = null;
  form.name = "";
  form.kind = "expense";
  form.description = "";
  form.color_token = "";
  form.is_default = false;
};

const removeCategory = async (row: any) => {
  const confirmed = window.confirm(`Delete category "${row.name}"?`);
  if (!confirmed) return;
  const response = await fetch(`${API_BASE}/categories/${row.id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    window.alert(payload?.detail || "Category could not be deleted.");
    return;
  }
  if (editingId.value === row.id) resetForm();
  await loadCategories();
};

onMounted(loadCategories);
</script>
