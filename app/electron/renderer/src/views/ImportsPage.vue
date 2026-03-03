<template>
  <main class="px-8 py-8">
    <div class="grid gap-6 lg:grid-cols-[420px_1fr]">
      <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Import Spreadsheet</h2>
        <p class="mt-1 text-xs text-slate-400">Upload data to persist in the local database for search and analytics.</p>

        <div class="mt-4">
          <label class="text-xs text-slate-400">Import Type</label>
          <select
            v-model="importType"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs"
          >
            <option value="generic">Generic Spreadsheet</option>
            <option value="payroll_summary">Payroll Summary Sections</option>
          </select>
        </div>

        <div v-if="importType === 'payroll_summary'" class="mt-4">
          <label class="text-xs text-slate-400">Mileage Cost Multiplier</label>
          <input
            v-model.number="mileageCost"
            type="number"
            step="0.01"
            min="0"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs"
          />
        </div>

        <div class="mt-4">
          <label class="inline-flex cursor-pointer items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400">
            Choose File
            <input type="file" class="hidden" accept=".xlsx,.xls,.csv" @change="onPickFile" />
          </label>
          <div v-if="selectedFile" class="mt-2 text-xs text-slate-300">{{ selectedFile.name }}</div>
        </div>

        <button
          class="mt-4 rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
          :disabled="!selectedFile || uploading"
          @click="uploadFile"
        >
          {{ uploading ? "Importing..." : "Import" }}
        </button>
        <button
          class="mt-2 rounded-md border border-rose-700 px-4 py-2 text-xs font-semibold text-rose-300 hover:border-rose-500 hover:text-rose-200"
          :disabled="clearing"
          @click="clearEmployeeData"
        >
          {{ clearing ? "Clearing..." : "Clear Employee Data" }}
        </button>

        <div v-if="uploadError" class="mt-3 text-sm text-rose-400">{{ uploadError }}</div>
        <div v-if="uploadResult" class="mt-3 text-xs text-emerald-300">
          Import complete: {{ uploadResult.row_count }} rows, {{ uploadResult.employees_identified }} employees.
        </div>
        <div v-if="clearMessage" class="mt-3 text-xs text-amber-300">{{ clearMessage }}</div>
      </section>

      <section class="space-y-4">
        <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Import History</h2>
            <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadImports">
              Refresh
            </button>
          </div>
          <div class="mt-4 overflow-x-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-4">File</th>
                  <th class="pb-2 pr-4">Rows</th>
                  <th class="pb-2 pr-4">Status</th>
                  <th class="pb-2">Uploaded</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in imports"
                  :key="item.id"
                  class="cursor-pointer border-t border-slate-800 text-slate-200 hover:bg-slate-800/40"
                  @click="selectImport(item.id)"
                >
                  <td class="py-2 pr-4">{{ item.filename }}</td>
                  <td class="py-2 pr-4">{{ item.row_count }}</td>
                  <td class="py-2 pr-4">{{ item.status }}</td>
                  <td class="py-2">{{ formatDate(item.uploaded_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="importStats" class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 class="text-sm font-semibold">Import Statistics</h3>
          <div class="mt-3 grid gap-3 sm:grid-cols-3 text-xs text-slate-300">
            <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
              <div class="text-slate-500">Employees</div>
              <div class="text-lg font-semibold">{{ importStats.summary.employees_count }}</div>
            </div>
            <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
              <div class="text-slate-500">Terapia</div>
              <div class="text-lg font-semibold">{{ importStats.summary.terapia_employees }}</div>
            </div>
            <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
              <div class="text-slate-500">Enfermeria</div>
              <div class="text-lg font-semibold">{{ importStats.summary.enfermeria_employees }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:8000";

const selectedFile = ref<File | null>(null);
const importType = ref<"generic" | "payroll_summary">("generic");
const mileageCost = ref(1);
const uploading = ref(false);
const clearing = ref(false);
const uploadError = ref("");
const uploadResult = ref<any>(null);
const clearMessage = ref("");

const imports = ref<any[]>([]);
const importStats = ref<any>(null);

const onPickFile = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0];
  }
};

const uploadFile = async () => {
  if (!selectedFile.value) return;
  uploading.value = true;
  uploadError.value = "";
  clearMessage.value = "";

  const payload = new FormData();
  payload.append("file", selectedFile.value);
  if (importType.value === "payroll_summary") {
    payload.append("mileage_cost", String(mileageCost.value));
  }

  try {
    const endpoint = importType.value === "payroll_summary" ? "/imports/payroll-summary" : "/imports";
    const response = await fetch(`${API_BASE}${endpoint}`, { method: "POST", body: payload });
    if (!response.ok) {
      const err = await response.json();
      uploadError.value = err.detail || "Import failed.";
      return;
    }
    uploadResult.value = await response.json();
    await loadImports();
  } catch {
    uploadError.value = "Failed to reach backend.";
  } finally {
    uploading.value = false;
  }
};

const loadImports = async () => {
  const response = await fetch(`${API_BASE}/imports`);
  imports.value = await response.json();
};

const clearEmployeeData = async () => {
  const confirmed = window.confirm("This will delete all imported employee data. Continue?");
  if (!confirmed) return;
  clearing.value = true;
  uploadError.value = "";
  clearMessage.value = "";
  try {
    const response = await fetch(`${API_BASE}/admin/clear-employee-data`, { method: "POST" });
    if (!response.ok) {
      const err = await response.json();
      uploadError.value = err.detail || "Failed to clear employee data.";
      return;
    }
    const data = await response.json();
    clearMessage.value = `Cleared ${data.deleted_imports} imports, ${data.deleted_entries} entries, ${data.deleted_employees} employees.`;
    uploadResult.value = null;
    importStats.value = null;
    await loadImports();
  } catch {
    uploadError.value = "Failed to reach backend.";
  } finally {
    clearing.value = false;
  }
};

const selectImport = async (importId: string) => {
  const response = await fetch(`${API_BASE}/imports/${importId}/stats`);
  if (!response.ok) return;
  importStats.value = await response.json();
};

const formatDate = (isoDate: string) => {
  try {
    return new Date(isoDate).toLocaleString();
  } catch {
    return isoDate;
  }
};

onMounted(async () => {
  await loadImports();
});
</script>
