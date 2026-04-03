<template>
  <main class="px-8 py-10">
    <section class="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 class="text-xl font-semibold">Operations Dashboard</h2>
          <p class="mt-1 text-sm text-slate-400">Active employee records, task mix, and daily spending trends.</p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <label class="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/70 px-3 py-2 text-xs text-slate-300">
            <input v-model="dashboardIncludeHistory" type="checkbox" />
            Include history
          </label>
          <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="loadMetrics">
            Refresh
          </button>
        </div>
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
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-white">Workspace Shortcuts</h3>
          <p class="mt-1 text-sm text-slate-400">Open the main areas people use every day.</p>
        </div>
        <router-link
          v-if="canSeeTools"
          to="/tools"
          class="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-xs font-semibold text-cyan-200 transition hover:border-cyan-300/50 hover:text-cyan-100"
        >
          Open Tools Center
        </router-link>
      </div>

      <div class="grid gap-6 sm:grid-cols-2">
        <div v-if="canManageImports" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
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
          <h2 class="text-xl font-semibold">Payments Workspace</h2>
          <p class="mt-2 text-sm text-slate-400">
            Track contractor and employee payments, upload payment backups, and build toward 480-ready totals.
          </p>
          <router-link
            to="/payments"
            class="mt-6 inline-flex items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400"
          >
            Open Payments
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Payment Profiles</h2>
          <p class="mt-2 text-sm text-slate-400">
            Maintain reusable payer and payee profiles so 480.6SP drafts can be generated from saved company and vendor details.
          </p>
          <router-link
            to="/payment-profiles"
            class="mt-6 inline-flex items-center rounded-md bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-cyan-400"
          >
            Open Payment Profiles
          </router-link>
        </div>
        <div v-if="canSeeTools" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Tools Center</h2>
          <p class="mt-2 text-sm text-slate-400">
            Open the report-generation workspace for the Employee Classifier and Payroll Summary Extractor.
          </p>
          <router-link
            to="/tools"
            class="mt-6 inline-flex items-center rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400"
          >
            Open Tools Center
          </router-link>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, watch } from "vue";
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
import { hasRoleAccess } from "../auth";
import { preferencesState, setDashboardIncludeHistory } from "../preferences";

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

const canSeeTools = computed(() => hasRoleAccess(["admin", "operator"]));
const canManageImports = computed(() => hasRoleAccess(["admin", "operator"]));
const dashboardIncludeHistory = computed({
  get: () => preferencesState.dashboardIncludeHistory,
  set: (value: boolean) => {
    setDashboardIncludeHistory(value);
  },
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
  const query = dashboardIncludeHistory.value ? "?include_history=true" : "";
  const response = await fetch(`${API_BASE}/dashboard/metrics${query}`);
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

watch(dashboardIncludeHistory, async () => {
  await loadMetrics();
});
</script>
