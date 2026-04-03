<template>
  <main class="grid gap-8 px-8 py-8 lg:grid-cols-[360px_1fr]">
    <section class="space-y-6">
      <div
        class="rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center"
        @dragover.prevent
        @drop.prevent="onDrop"
      >
        <div class="text-sm text-slate-300">Drag and drop a spreadsheet (.xlsx, .xls, .csv)</div>
        <div class="mt-2 text-xs text-slate-500">or</div>
        <label class="mt-4 inline-flex cursor-pointer items-center justify-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400">
          Choose File
          <input type="file" class="hidden" accept=".xlsx,.xls,.csv" @change="onFilePick" />
        </label>
        <div v-if="selectedFile" class="mt-4 text-xs text-slate-300">Selected: {{ selectedFile.name }}</div>
        <div class="mt-6 flex justify-center">
          <button
            class="rounded-md bg-indigo-500 px-5 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            :disabled="!selectedFile || processing"
            @click="processFile"
          >
            {{ processing ? "Processing..." : "Process File" }}
          </button>
        </div>
        <div class="mt-4 text-left text-sm">
          <label class="text-xs text-slate-400">Mileage Cost Multiplier</label>
          <input
            v-model.number="mileagePreference"
            type="number"
            step="0.01"
            min="0"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
          />
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Payroll Summary Classifier</h2>
        <p class="mt-1 text-xs text-slate-400">
          Detects employee blocks after "Payroll Summary", classifies by Task tokens, and generates totals.
        </p>
      </div>

      <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 class="text-lg font-semibold">Results</h2>
        <div v-if="error" class="mt-2 text-sm text-red-400">{{ error }}</div>

        <h3 v-if="summary" class="mt-4 text-sm font-semibold text-slate-200">Statistics</h3>
        <div v-if="summary" class="mt-4 grid gap-3 sm:grid-cols-3 text-xs text-slate-300">
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Rows</div>
            <div class="text-lg font-semibold">{{ summary.total_rows }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Payroll Summary Markers</div>
            <div class="text-lg font-semibold">{{ summary.marker_count }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Employees Identified</div>
            <div class="text-lg font-semibold">{{ summary.employees_identified }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Terapia Employees</div>
            <div class="text-lg font-semibold">{{ summary.terapia_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Enfermeria Employees</div>
            <div class="text-lg font-semibold">{{ summary.enfermeria_employees }}</div>
          </div>
          <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
            <div class="text-slate-500">Unclassified Employees</div>
            <div class="text-lg font-semibold text-amber-300">{{ summary.unclassified_employees }}</div>
          </div>
        </div>

        <div class="mt-6">
          <button
            class="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-slate-500 disabled:cursor-not-allowed"
            :disabled="!reportId"
            @click="downloadReport"
          >
            Download Report (xlsx)
          </button>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";

import { authHeaders } from "../auth";
import { useMileagePreference } from "../preferences";

const API_BASE = "http://127.0.0.1:8000";

const selectedFile = ref<File | null>(null);
const processing = ref(false);
const reportId = ref("");
const error = ref("");
const summary = ref<any>(null);
const mileagePreference = useMileagePreference();

const onFilePick = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0];
  }
};

const onDrop = (event: DragEvent) => {
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
};

const processFile = async () => {
  if (!selectedFile.value) return;
  processing.value = true;
  error.value = "";

  const payload = new FormData();
  payload.append("file", selectedFile.value);
  payload.append("mileage_cost", String(mileagePreference.value));

  try {
    const response = await fetch(`${API_BASE}/process-payroll-summary`, {
      method: "POST",
      body: payload,
      headers: authHeaders(),
    });
    if (!response.ok) {
      const data = await response.json();
      error.value = data.detail || "Processing failed.";
      return;
    }

    const data = await response.json();
    summary.value = data.summary;
    reportId.value = data.report_id;
  } catch {
    error.value = "Failed to reach the processing service.";
  } finally {
    processing.value = false;
  }
};

const downloadReport = async () => {
  if (!reportId.value) return;

  const response = await fetch(`${API_BASE}/report/${reportId.value}`);
  if (!response.ok) {
    error.value = "Failed to download report.";
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "payroll_summary_report.xlsx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};
</script>
