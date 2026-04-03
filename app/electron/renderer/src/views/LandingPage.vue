<template>
  <main class="px-8 py-10">
    <section class="tp-glass rounded-[28px] bg-[radial-gradient(circle_at_top_left,_rgba(103,232,249,0.12),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(167,139,250,0.1),_transparent_22%),linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/75">Business Hub</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight">Operations Dashboard</h2>
          <p class="mt-3 text-sm font-semibold uppercase tracking-[0.26em] text-cyan-200/90">
            Accountability, fast tracking, and automated financial deployment.
          </p>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">Run daily operations, document intake, vendor and employee tracking, and Puerto Rico compliance from one aligned workflow.</p>
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

      <div class="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div class="tp-panel rounded-3xl p-5">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Suggested Workflow</div>
          <div class="mt-4 grid gap-3 md:grid-cols-4">
            <router-link to="/documents" class="tp-panel-soft rounded-2xl p-4 transition hover:border-cyan-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-cyan-300">1. Collect</div>
              <div class="mt-2 text-sm font-semibold text-white">Documents</div>
              <div class="mt-2 text-xs text-slate-400">Start from uploads and recent files.</div>
            </router-link>
            <router-link to="/transactions" class="tp-panel-soft rounded-2xl p-4 transition hover:border-cyan-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-emerald-300">2. Classify</div>
              <div class="mt-2 text-sm font-semibold text-white">Transactions</div>
              <div class="mt-2 text-xs text-slate-400">Review outgoing business activity.</div>
            </router-link>
            <router-link to="/bills-expenses" class="tp-panel-soft rounded-2xl p-4 transition hover:border-amber-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-amber-300">3. Track</div>
              <div class="mt-2 text-sm font-semibold text-white">Bills & Expenses</div>
              <div class="mt-2 text-xs text-slate-400">Capture bills and payable activity.</div>
            </router-link>
            <router-link to="/vendors" class="tp-panel-soft rounded-2xl p-4 transition hover:border-violet-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-amber-300">4. Maintain</div>
              <div class="mt-2 text-sm font-semibold text-white">Vendors</div>
              <div class="mt-2 text-xs text-slate-400">Keep payees and contacts clean.</div>
            </router-link>
          </div>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <router-link to="/employees" class="tp-panel-soft rounded-2xl p-4 transition hover:border-cyan-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-sky-300">5. Operate</div>
              <div class="mt-2 text-sm font-semibold text-white">Employees</div>
              <div class="mt-2 text-xs text-slate-400">Review employee activity and internal records.</div>
            </router-link>
            <router-link to="/form-480-prep" class="tp-panel-soft rounded-2xl p-4 transition hover:border-violet-400/40">
              <div class="text-[11px] uppercase tracking-[0.2em] text-violet-300">6. File</div>
              <div class="mt-2 text-sm font-semibold text-white">Compliance</div>
              <div class="mt-2 text-xs text-slate-400">Generate 480.6SP drafts and review issues.</div>
            </router-link>
          </div>
        </div>

        <div class="tp-panel rounded-3xl p-5">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Today</div>
          <div class="mt-4 space-y-3 text-sm text-slate-300">
            <div class="tp-kpi rounded-2xl p-4">
              <div class="text-xs uppercase tracking-[0.2em] text-slate-500">Documents</div>
              <div class="mt-2 text-xl font-semibold text-white">{{ businessOverview.totals.payment_imports_count + businessOverview.totals.spreadsheet_imports_count }}</div>
              <div class="mt-1 text-xs text-slate-400">Uploaded business files across operations and payments.</div>
            </div>
            <div class="tp-kpi rounded-2xl p-4">
              <div class="text-xs uppercase tracking-[0.2em] text-slate-500">Vendors</div>
              <div class="mt-2 text-xl font-semibold text-white">{{ businessOverview.totals.payees_count }}</div>
              <div class="mt-1 text-xs text-slate-400">Tracked payees ready for payment and compliance workflows.</div>
            </div>
            <div class="tp-kpi rounded-2xl p-4">
              <div class="text-xs uppercase tracking-[0.2em] text-slate-500">Current Year Spend</div>
              <div class="mt-2 text-xl font-semibold text-white">{{ currency(businessOverview.totals.current_year_payment_total) }}</div>
              <div class="mt-1 text-xs text-slate-400">Outgoing service payments in the current filing year.</div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 tp-panel rounded-3xl p-5">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Dashboard Filters</div>
            <p class="mt-2 text-sm text-slate-400">Focus the graphs by date, company, payee, or transaction type without leaving the overview.</p>
          </div>
          <button
            class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500"
            @click="clearFilters"
          >
            Clear Filters
          </button>
        </div>

        <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label class="flex flex-col gap-2 text-xs text-slate-300">
            <span class="uppercase tracking-[0.18em] text-slate-500">Date From</span>
            <input v-model="dashboardFilters.dateFrom" type="date" class="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50" />
          </label>
          <label class="flex flex-col gap-2 text-xs text-slate-300">
            <span class="uppercase tracking-[0.18em] text-slate-500">Date To</span>
            <input v-model="dashboardFilters.dateTo" type="date" class="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50" />
          </label>
          <label class="flex flex-col gap-2 text-xs text-slate-300">
            <span class="uppercase tracking-[0.18em] text-slate-500">Company</span>
            <select v-model="dashboardFilters.companyId" class="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50">
              <option value="">All companies</option>
              <option v-for="company in filterOptions.companies" :key="company.id" :value="String(company.id)">{{ company.name }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-2 text-xs text-slate-300">
            <span class="uppercase tracking-[0.18em] text-slate-500">Payee</span>
            <select v-model="dashboardFilters.payeeId" class="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50">
              <option value="">All payees</option>
              <option v-for="payee in filterOptions.payees" :key="payee.id" :value="String(payee.id)">{{ payee.name }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-2 text-xs text-slate-300">
            <span class="uppercase tracking-[0.18em] text-slate-500">Transaction Type</span>
            <select v-model="dashboardFilters.transactionType" class="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50">
              <option value="">All types</option>
              <option v-for="type in filterOptions.transactionTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
        </div>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-8 text-xs text-slate-300">
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Employees</div>
          <div class="text-lg font-semibold">{{ metrics.totals.employees_count }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Payees</div>
          <div class="text-lg font-semibold">{{ metrics.totals.payees_count }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Companies</div>
          <div class="text-lg font-semibold">{{ metrics.totals.companies_count }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Transactions</div>
          <div class="text-lg font-semibold">{{ metrics.totals.transactions_count }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Employee Rows</div>
          <div class="text-lg font-semibold">{{ metrics.totals.rows_count }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Rate Total</div>
          <div class="text-lg font-semibold">{{ currency(metrics.totals.rate_total) }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Mileage Total</div>
          <div class="text-lg font-semibold">{{ number(metrics.totals.mileage_total) }}</div>
        </div>
        <div class="tp-kpi rounded-lg p-3">
          <div class="text-slate-500">Amount Total</div>
          <div class="text-lg font-semibold">{{ currency(metrics.totals.amount_total) }}</div>
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Employee Classification</h3>
          <div class="mt-3 h-56">
            <Bar v-if="classChartData.labels.length" :data="classChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Top Payees by Spend</h3>
          <div class="mt-3 h-56">
            <Bar v-if="payeeChartData.labels.length" :data="payeeChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Company Deployment</h3>
          <div class="mt-3 h-56">
            <Bar v-if="companyChartData.labels.length" :data="companyChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Transaction Types</h3>
          <div class="mt-3 h-56">
            <Bar v-if="transactionTypeChartData.labels.length" :data="transactionTypeChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Employee Rate by Date</h3>
          <div class="mt-3 h-56">
            <Line v-if="rateTrendData.labels.length" :data="rateTrendData" :options="lineChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>

        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Financial Deployment by Date</h3>
          <div class="mt-3 h-56">
            <Line v-if="businessTrendData.labels.length" :data="businessTrendData" :options="lineChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>
      </div>

      <div class="mt-6 grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <h3 class="text-sm font-semibold text-slate-200">Employee Tasks by Rows</h3>
          <div class="mt-3 h-56">
            <Bar v-if="taskChartData.labels.length" :data="taskChartData" :options="baseChartOptions" />
            <div v-else class="text-xs text-slate-500">No data yet.</div>
          </div>
        </div>
      </div>
    </section>

    <section class="mt-8">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-lg font-semibold text-white">Module Shortcuts</h3>
          <p class="mt-1 text-sm text-slate-400">Move through the app the way a small business workflow naturally flows.</p>
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
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Documents</h2>
          <p class="mt-2 text-sm text-slate-400">
            Centralize payment backups, payroll files, and imported operational documents.
          </p>
          <router-link
            to="/documents"
            class="mt-6 inline-flex items-center rounded-md bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-cyan-400"
          >
            Open Documents
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Transactions</h2>
          <p class="mt-2 text-sm text-slate-400">
            See business spend in a searchable transaction view built from your payment data.
          </p>
          <router-link
            to="/transactions"
            class="mt-6 inline-flex items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400"
          >
            Open Transactions
          </router-link>
        </div>
        <div v-if="canSeeTools" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Bills & Expenses</h2>
          <p class="mt-2 text-sm text-slate-400">
            Create bills and expenses in the shared ledger so payables, receipts, and purchases are tracked alongside payments.
          </p>
          <router-link
            to="/bills-expenses"
            class="mt-6 inline-flex items-center rounded-md bg-rose-400 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-rose-300"
          >
            Open Bills & Expenses
          </router-link>
        </div>
        <div v-if="canManageImports" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Categories</h2>
          <p class="mt-2 text-sm text-slate-400">
            Keep category mapping reusable across receipt review, bills, and shared transaction reporting.
          </p>
          <router-link
            to="/categories"
            class="mt-6 inline-flex items-center rounded-md bg-violet-400 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-violet-300"
          >
            Open Categories
          </router-link>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-[0_20px_60px_-35px_rgba(15,23,42,0.6)]">
          <h2 class="text-xl font-semibold">Vendors</h2>
          <p class="mt-2 text-sm text-slate-400">
            Maintain vendor and payee records that support payments, receipts, and year-end prep.
          </p>
          <router-link
            to="/vendors"
            class="mt-6 inline-flex items-center rounded-md bg-amber-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-amber-400"
          >
            Open Vendors
          </router-link>
        </div>
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
    companies_count: 0,
    payees_count: 0,
    transactions_count: 0,
  },
  by_classification: [],
  by_task: [],
  by_date: [],
  by_payee: [],
  by_company: [],
  by_transaction_type: [],
  business_by_date: [],
});
const businessOverview = reactive<any>({
  totals: {
    payment_imports_count: 0,
    spreadsheet_imports_count: 0,
    payees_count: 0,
    current_year_payment_total: 0,
  },
});
const filterOptions = reactive<{ companies: Array<{ id: number; name: string }>; payees: Array<{ id: number; name: string }>; transactionTypes: string[] }>({
  companies: [],
  payees: [],
  transactionTypes: [],
});
const dashboardFilters = reactive({
  dateFrom: "",
  dateTo: "",
  companyId: "",
  payeeId: "",
  transactionType: "",
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

const payeeChartData = computed(() => ({
  labels: metrics.by_payee.map((x: any) => x.label),
  datasets: [
    {
      label: "Amount",
      data: metrics.by_payee.map((x: any) => x.amount_total || 0),
      backgroundColor: "rgba(103, 232, 249, 0.75)",
      borderRadius: 4,
    },
  ],
}));

const companyChartData = computed(() => ({
  labels: metrics.by_company.map((x: any) => x.label),
  datasets: [
    {
      label: "Amount",
      data: metrics.by_company.map((x: any) => x.amount_total || 0),
      backgroundColor: "rgba(167, 139, 250, 0.75)",
      borderRadius: 4,
    },
  ],
}));

const transactionTypeChartData = computed(() => ({
  labels: metrics.by_transaction_type.map((x: any) => x.label),
  datasets: [
    {
      label: "Amount",
      data: metrics.by_transaction_type.map((x: any) => x.amount_total || 0),
      backgroundColor: "rgba(245, 158, 11, 0.75)",
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

const businessTrendData = computed(() => ({
  labels: metrics.business_by_date.map((x: any) => x.date),
  datasets: [
    {
      label: "Amount",
      data: metrics.business_by_date.map((x: any) => x.amount_total || 0),
      borderColor: "rgba(167, 139, 250, 1)",
      backgroundColor: "rgba(167, 139, 250, 0.18)",
      tension: 0.3,
      fill: true,
    },
  ],
}));

const loadFilterOptions = async () => {
  const response = await fetch(`${API_BASE}/dashboard/filter-options`);
  if (!response.ok) return;
  const data = await response.json();
  filterOptions.companies = data.companies || [];
  filterOptions.payees = data.payees || [];
  filterOptions.transactionTypes = data.transaction_types || [];
};

const loadMetrics = async () => {
  const params = new URLSearchParams();
  if (dashboardIncludeHistory.value) params.set("include_history", "true");
  if (dashboardFilters.dateFrom) params.set("date_from", dashboardFilters.dateFrom);
  if (dashboardFilters.dateTo) params.set("date_to", dashboardFilters.dateTo);
  if (dashboardFilters.companyId) params.set("company_id", dashboardFilters.companyId);
  if (dashboardFilters.payeeId) params.set("payee_id", dashboardFilters.payeeId);
  if (dashboardFilters.transactionType) params.set("transaction_type", dashboardFilters.transactionType);
  const query = params.toString() ? `?${params.toString()}` : "";
  const [metricsResponse, overviewResponse] = await Promise.all([
    fetch(`${API_BASE}/dashboard/metrics${query}`),
    fetch(`${API_BASE}/business/overview`),
  ]);
  if (metricsResponse.ok) {
    const data = await metricsResponse.json();
    metrics.totals = data.totals;
    metrics.by_classification = data.by_classification || [];
    metrics.by_task = data.by_task || [];
    metrics.by_date = data.by_date || [];
    metrics.by_payee = data.by_payee || [];
    metrics.by_company = data.by_company || [];
    metrics.by_transaction_type = data.by_transaction_type || [];
    metrics.business_by_date = data.business_by_date || [];
  }
  if (overviewResponse.ok) {
    const overview = await overviewResponse.json();
    businessOverview.totals = overview.totals || businessOverview.totals;
  }
};

const clearFilters = async () => {
  dashboardFilters.dateFrom = "";
  dashboardFilters.dateTo = "";
  dashboardFilters.companyId = "";
  dashboardFilters.payeeId = "";
  dashboardFilters.transactionType = "";
  await loadMetrics();
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

const number = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(Number(value || 0));

onMounted(async () => {
  await loadFilterOptions();
  await loadMetrics();
});

watch([dashboardIncludeHistory, () => dashboardFilters.dateFrom, () => dashboardFilters.dateTo, () => dashboardFilters.companyId, () => dashboardFilters.payeeId, () => dashboardFilters.transactionType], async () => {
  await loadMetrics();
});
</script>
