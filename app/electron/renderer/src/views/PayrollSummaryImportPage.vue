<template>
  <main class="px-8 py-8">
    <div class="grid gap-6 lg:grid-cols-[420px_1fr]">
      <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Payroll Summary Importer</h2>
        <p class="mt-1 text-xs text-slate-400">
          Parses Payroll Summary sections and stores per-row employee data by date.
        </p>

        <div class="mt-4">
          <label class="inline-flex cursor-pointer items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400">
            Choose File
            <input type="file" class="hidden" accept=".xlsx,.xls,.csv" @change="onPickFile" />
          </label>
          <div v-if="selectedFile" class="mt-2 text-xs text-slate-300">{{ selectedFile.name }}</div>
        </div>

        <div class="mt-4">
          <label class="text-xs text-slate-400">Mileage Cost Multiplier</label>
          <input
            v-model.number="mileageCost"
            type="number"
            step="0.01"
            min="0"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs"
          />
        </div>

        <button
          class="mt-4 rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
          :disabled="!selectedFile || uploading"
          @click="uploadFile"
        >
          {{ uploading ? "Importing..." : "Import Payroll Summary" }}
        </button>

        <div v-if="uploadError" class="mt-3 text-sm text-rose-400">{{ uploadError }}</div>
        <div v-if="uploadResult" class="mt-3 text-xs text-emerald-300">
          Imported {{ uploadResult.row_count }} rows for {{ uploadResult.employees_identified }} employees.
        </div>
      </section>

      <section class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Import Result</h2>
        <div v-if="uploadResult" class="mt-4 grid gap-3 sm:grid-cols-2 text-xs text-slate-300">
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Rows</div>
            <div class="text-lg font-semibold">{{ uploadResult.row_count }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Employees</div>
            <div class="text-lg font-semibold">{{ uploadResult.employees_identified }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Terapia</div>
            <div class="text-lg font-semibold">{{ uploadResult.terapia_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Enfermeria</div>
            <div class="text-lg font-semibold">{{ uploadResult.enfermeria_employees }}</div>
          </div>
        </div>

        <router-link
          to="/records"
          class="mt-6 inline-flex items-center rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500"
        >
          Open Records Table
        </router-link>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";

const API_BASE = "http://127.0.0.1:8000";

const selectedFile = ref<File | null>(null);
const mileageCost = ref(1);
const uploading = ref(false);
const uploadError = ref("");
const uploadResult = ref<any>(null);

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

  const payload = new FormData();
  payload.append("file", selectedFile.value);
  payload.append("mileage_cost", String(mileageCost.value));

  try {
    const response = await fetch(`${API_BASE}/imports/payroll-summary`, { method: "POST", body: payload });
    if (!response.ok) {
      const err = await response.json();
      uploadError.value = err.detail || "Import failed.";
      return;
    }
    uploadResult.value = await response.json();
  } catch {
    uploadError.value = "Failed to reach backend.";
  } finally {
    uploading.value = false;
  }
};
</script>
