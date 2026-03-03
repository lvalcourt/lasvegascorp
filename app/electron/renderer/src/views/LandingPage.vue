<template>
  <main class="px-8 py-10">
    <section class="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold">Operations Dashboard</h2>
          <p class="mt-1 text-sm text-slate-400">Active employee records, task mix, and daily spending trends.</p>
        </div>
        <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadMetrics">
          Refresh
        </button>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6 text-xs text-slate-300">
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Employees</div>
          <div class="text-lg font-semibold">{{ metrics.totals.employees_count }}</div>
        </div>
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Rows</div>
          <div class="text-lg font-semibold">{{ metrics.totals.rows_count }}</div>
        </div>
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Rate Total</div>
          <div class="text-lg font-semibold">{{ currency(metrics.totals.rate_total) }}</div>
        </div>
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Mileage Total</div>
          <div class="text-lg font-semibold">{{ number(metrics.totals.mileage_total) }}</div>
        </div>
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Surcharge Total</div>
          <div class="text-lg font-semibold">{{ currency(metrics.totals.surcharge_total) }}</div>
        </div>
        <div class="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
          <div class="text-slate-500">Amount Total</div>
          <div class="text-lg font-semibold">{{ currency(metrics.totals.amount_total) }}</div>
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Employee Classification</h3>
          <div class="mt-3 h-56">
            <Bar v-if="classChartData.labels.length" :data="classChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Top Tasks by Rows</h3>
          <div class="mt-3 h-56">
            <Bar v-if="taskChartData.labels.length" :data="taskChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Rate Spend by Date</h3>
          <div class="mt-3 h-56">
            <Line v-if="rateTrendData.labels.length" :data="rateTrendData" :options="lineChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Patients Visited by Date</h3>
          <div class="mt-3 h-56">
            <Line v-if="patientTrendData.labels.length" :data="patientTrendData" :options="lineChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-8">
      <div class="grid gap-6 sm:grid-cols-2">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Imports Workspace</h2>
          <p class="mt-2 text-sm text-slate-400">
            Ingest spreadsheets into the local database for daily usage and analytics.
          </p>
          <router-link
            to="/imports"
            class="mt-6 inline-flex items-center rounded-md bg-sky-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-sky-400"
          >
            Open Imports
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Employees Workspace</h2>
          <p class="mt-2 text-sm text-slate-400">
            Search employees and traverse historical data from imported spreadsheets.
          </p>
          <router-link
            to="/employees"
            class="mt-6 inline-flex items-center rounded-md bg-amber-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-amber-400"
          >
            Open Employees
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Employee Classifier Tool</h2>
          <p class="mt-2 text-sm text-slate-400">
            Classify employee records, apply rules, and export reports.
          </p>
          <router-link
            to="/payroll"
            class="mt-6 inline-flex items-center rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400"
          >
            Open Employee Classifier Tool
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Payroll Summary Extractor</h2>
          <p class="mt-2 text-sm text-slate-400">
            Read employee sections after Payroll Summary markers and generate employee totals.
          </p>
          <router-link
            to="/payroll-summary"
            class="mt-6 inline-flex items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400"
          >
            Open Payroll Summary Extractor
          </router-link>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from "vue";
import { Bar, Line } from "vue-chartjs";
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  BarElement,
  Title,
  Tooltip,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const API_BASE = "http://127.0.0.1:8000";

const metrics = reactive<any>({
  totals: {
    rows_count: 0,
    employees_count: 0,
    rate_total: 0,
    mileage_total: 0,
    surcharge_total: 0,
    amount_total: 0,
  },
  by_classification: [],
  by_task: [],
  by_date: [],
});

const baseChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false, labels: { color: "#cbd5e1" } },
  },
  scales: {
    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.15)" } },
    y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.15)" } },
  },
};

const lineChartOptions = {
  ...baseChartOptions,
  plugins: {
    legend: { display: false, labels: { color: "#cbd5e1" } },
  },
};

const classChartData = computed(() => ({
  labels: metrics.by_classification.map((x: any) => x.label),
  datasets: [
    {
      label: "Employees",
      data: metrics.by_classification.map((x: any) => x.employees_count),
      backgroundColor: "rgba(56, 189, 248, 0.75)",
      borderRadius: 4,
    },
  ],
}));

const taskChartData = computed(() => ({
  labels: metrics.by_task.map((x: any) => x.label),
  datasets: [
    {
      label: "Rows",
      data: metrics.by_task.map((x: any) => x.rows_count),
      backgroundColor: "rgba(52, 211, 153, 0.75)",
      borderRadius: 4,
    },
  ],
}));

const rateTrendData = computed(() => ({
  labels: metrics.by_date.map((x: any) => x.date),
  datasets: [
    {
      label: "Rate Total",
      data: metrics.by_date.map((x: any) => x.rate_total || 0),
      borderColor: "rgba(96, 165, 250, 1)",
      backgroundColor: "rgba(96, 165, 250, 0.2)",
      tension: 0.3,
      fill: true,
    },
  ],
}));

const patientTrendData = computed(() => ({
  labels: metrics.by_date.map((x: any) => x.date),
  datasets: [
    {
      label: "Patients",
      data: metrics.by_date.map((x: any) => x.patients_count || 0),
      borderColor: "rgba(251, 191, 36, 1)",
      backgroundColor: "rgba(251, 191, 36, 0.2)",
      tension: 0.3,
      fill: true,
    },
  ],
}));

const loadMetrics = async () => {
  const response = await fetch(`${API_BASE}/dashboard/metrics`);
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  metrics.totals = data.totals;
  metrics.by_classification = data.by_classification || [];
  metrics.by_task = data.by_task || [];
  metrics.by_date = data.by_date || [];
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

const number = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(Number(value || 0));

onMounted(async () => {
  await loadMetrics();
});
</script>
