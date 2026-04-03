<template>
  <main class="px-8 py-8">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-300/75">SURI 480.6SP Prep</p>
          <h2 class="mt-4 text-3xl font-semibold tracking-tight text-white">Review services-rendered totals before filing.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            This view is now focused on Form 480.6SP for services rendered. It helps users identify payees, yearly totals, missing tax IDs, and which payees are closest to autofill-ready packets.
          </p>
        </div>

        <div class="flex items-center gap-3">
          <input v-model.number="taxYear" type="number" min="2000" step="1" class="w-32 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" />
          <label class="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-950/80 px-4 py-3 text-xs text-slate-300">
            <input v-model="includeHistory" type="checkbox" />
            Include history
          </label>
          <button class="rounded-2xl bg-amber-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-300" @click="loadSummary">
            Refresh
          </button>
        </div>
      </div>

      <div class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-slate-800 bg-slate-950/75 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Tax Year</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ summary.tax_year }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/75 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Payment Records</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ summary.totals.records_count }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/75 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Payees</div>
          <div class="mt-2 text-2xl font-semibold text-white">{{ summary.totals.payees_count }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/75 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Missing Tax IDs</div>
          <div class="mt-2 text-2xl font-semibold text-amber-300">{{ summary.totals.payees_missing_tax_id }}</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/75 p-4">
          <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Autofill Ready</div>
          <div class="mt-2 text-2xl font-semibold text-emerald-300">{{ summary.totals.payees_ready }}</div>
        </div>
      </div>

      <div class="mt-6 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-white">480.6SP Payee Readiness</h3>
          <div class="text-sm text-slate-300">Total Paid: {{ currency(summary.totals.amount_total) }}</div>
        </div>

        <div class="mt-4 overflow-auto">
          <table class="min-w-full text-left text-xs">
            <thead class="text-slate-400">
              <tr>
                <th class="pb-2 pr-3">Payee</th>
                <th class="pb-2 pr-3">Tax ID</th>
                <th class="pb-2 pr-3">Payments</th>
                <th class="pb-2 pr-3">Total</th>
                <th class="pb-2 pr-3">Issues</th>
                <th class="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summary.payees" :key="`${row.payee_name}-${row.tax_id || 'missing'}`" class="border-t border-slate-800 text-slate-200">
                <td class="py-2 pr-3">{{ row.payee_name }}</td>
                <td class="py-2 pr-3">{{ row.tax_id || "" }}</td>
                <td class="py-2 pr-3">{{ row.payments_count }}</td>
                <td class="py-2 pr-3">{{ currency(row.amount_total) }}</td>
                <td class="py-2 pr-3">
                  <span v-if="row.issues?.length">{{ row.issues.join(", ") }}</span>
                  <span v-else class="text-slate-500">None</span>
                </td>
                <td class="py-2">
                  <span
                    class="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold"
                    :class="row.ready ? 'bg-emerald-400/15 text-emerald-200' : 'bg-amber-400/15 text-amber-200'"
                  >
                    {{ row.ready ? "Ready for prefill" : "Needs review" }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="mt-6 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-white">Prefill Packet</h3>
            <p class="mt-1 text-xs text-slate-400">Select a payee to inspect the structured payload we’ll later bind to the official fillable PDF.</p>
          </div>
          <select v-model.number="selectedPayeeId" class="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white">
            <option :value="0">Choose payee</option>
            <option v-for="row in summary.payees" :key="row.payee_id" :value="row.payee_id">
              {{ row.payee_name }}
            </option>
          </select>
        </div>

        <div v-if="prefillPacket" class="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
          <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-xs text-slate-300">
            <div class="text-[11px] uppercase tracking-[0.2em] text-slate-500">Packet Status</div>
            <div class="mt-3 flex items-center gap-2">
              <span
                class="inline-flex rounded-full px-3 py-1 text-[11px] font-semibold"
                :class="prefillPacket.autofill_ready ? 'bg-emerald-400/15 text-emerald-200' : 'bg-amber-400/15 text-amber-200'"
              >
                {{ prefillPacket.autofill_ready ? "Autofill-ready packet" : "Needs more data" }}
              </span>
            </div>
            <ul class="mt-3 space-y-2">
              <li v-for="issue in prefillPacket.issues" :key="issue">{{ issue }}</li>
              <li v-if="!prefillPacket.issues.length" class="text-slate-500">No blocking issues found.</li>
            </ul>
            <button
              class="mt-4 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-xs font-semibold text-emerald-200 transition hover:border-emerald-300/50 hover:text-emerald-100"
              @click="downloadDraftPdf"
            >
              Download 480.6SP Draft PDF
            </button>
          </div>

          <pre class="overflow-auto rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-[11px] leading-5 text-slate-300">{{ JSON.stringify(prefillPacket.prefill_packet, null, 2) }}</pre>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

const API_BASE = "http://127.0.0.1:8000";

const taxYear = ref(new Date().getFullYear());
const includeHistory = ref(false);
const summary = reactive<any>({
  tax_year: new Date().getFullYear(),
  totals: {
    records_count: 0,
    payees_count: 0,
    amount_total: 0,
    payees_missing_tax_id: 0,
    payees_ready: 0,
  },
  payees: [],
});
const selectedPayeeId = ref(0);
const prefillPacket = ref<any>(null);

const loadSummary = async () => {
  const params = new URLSearchParams({ tax_year: String(taxYear.value) });
  if (includeHistory.value) params.append("include_history", "true");
  const response = await fetch(`${API_BASE}/payments/4806sp/summary?${params.toString()}`);
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  summary.tax_year = data.tax_year;
  summary.totals = data.totals;
  summary.payees = data.payees || [];
  if (selectedPayeeId.value) {
    await loadPrefillPacket();
  }
};

const loadPrefillPacket = async () => {
  if (!selectedPayeeId.value) {
    prefillPacket.value = null;
    return;
  }
  const params = new URLSearchParams({ tax_year: String(taxYear.value) });
  if (includeHistory.value) params.append("include_history", "true");
  const response = await fetch(`${API_BASE}/payments/4806sp/payees/${selectedPayeeId.value}/prefill?${params.toString()}`);
  if (!response.ok) {
    prefillPacket.value = null;
    return;
  }
  prefillPacket.value = await response.json();
};

const downloadDraftPdf = async () => {
  if (!selectedPayeeId.value) return;
  const params = new URLSearchParams({ tax_year: String(taxYear.value) });
  if (includeHistory.value) params.append("include_history", "true");
  const response = await fetch(`${API_BASE}/payments/4806sp/payees/${selectedPayeeId.value}/draft-pdf?${params.toString()}`);
  if (!response.ok) {
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `480.6SP_draft_${selectedPayeeId.value}_${taxYear.value}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const currency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));

onMounted(async () => {
  await loadSummary();
});

watch([selectedPayeeId, taxYear, includeHistory], async () => {
  await loadPrefillPacket();
});
</script>
