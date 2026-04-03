<template>
  <main class="px-8 py-8">
    <div class="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <section class="space-y-6">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-white">Company Profiles</h2>
              <p class="mt-1 text-xs text-slate-400">Store legal company information separately from filing payer profiles.</p>
            </div>
            <div class="flex gap-2">
              <button
                v-if="canEdit"
                class="rounded-md border border-amber-600 px-3 py-1.5 text-xs font-semibold text-amber-200 hover:border-amber-400"
                :disabled="seedingDemo"
                @click="seedDemoData"
              >
                {{ seedingDemo ? "Seeding..." : "Load Demo Data" }}
              </button>
              <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="resetCompanyEditor">New Company</button>
            </div>
          </div>
          <p v-if="seedMessage" class="mt-3 text-xs text-emerald-300">{{ seedMessage }}</p>
          <p v-if="seedError" class="mt-3 text-xs text-rose-300">{{ seedError }}</p>

          <div class="mt-4 max-h-52 overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">Name</th>
                  <th class="pb-2 pr-3">Tax ID</th>
                  <th class="pb-2">Default</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in companies" :key="row.id" class="cursor-pointer border-t border-slate-800 text-slate-200 hover:bg-slate-800/40" @click="editCompany(row)">
                  <td class="py-2 pr-3">{{ row.name }}</td>
                  <td class="py-2 pr-3">{{ row.tax_id || "" }}</td>
                  <td class="py-2">{{ row.is_default ? "Yes" : "" }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <form class="mt-4 space-y-3" @submit.prevent="saveCompany">
            <input v-model="companyEditor.name" type="text" placeholder="Company name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="companyEditor.legal_name" type="text" placeholder="Legal name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="companyEditor.tax_id" type="text" placeholder="Tax ID" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="companyEditor.address_line1" type="text" placeholder="Address line 1" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="companyEditor.address_line2" type="text" placeholder="Address line 2" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <div class="grid gap-3 sm:grid-cols-3">
              <input v-model="companyEditor.city" type="text" placeholder="City" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="companyEditor.state" type="text" placeholder="State" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="companyEditor.zip_code" type="text" placeholder="Zip code" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="companyEditor.email" type="email" placeholder="Email" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="companyEditor.phone" type="text" placeholder="Phone" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <label class="inline-flex items-center gap-2 text-xs text-slate-300">
              <input v-model="companyEditor.is_default" type="checkbox" :disabled="!canEdit" />
              Set as default company
            </label>
            <div class="flex gap-2">
              <button class="rounded-md bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-slate-700" :disabled="!canEdit || savingCompany">
                {{ savingCompany ? "Saving..." : companyEditor.id ? "Update Company" : "Create Company" }}
              </button>
              <button type="button" class="rounded-md border border-rose-700 px-4 py-2 text-xs font-semibold text-rose-300 hover:border-rose-500 disabled:cursor-not-allowed disabled:text-slate-500" :disabled="!canEdit || !companyEditor.id" @click="deleteCompany">
                Delete
              </button>
            </div>
          </form>
        </div>

        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-white">Payer Profiles</h2>
              <p class="mt-1 text-xs text-slate-400">Choose which filing identity should be used for 480.6SP drafts.</p>
            </div>
            <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="resetPayerEditor">New Payer</button>
          </div>

          <div class="mt-4 max-h-52 overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">Name</th>
                  <th class="pb-2 pr-3">Company</th>
                  <th class="pb-2">Default</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in payers" :key="row.id" class="cursor-pointer border-t border-slate-800 text-slate-200 hover:bg-slate-800/40" @click="editPayer(row)">
                  <td class="py-2 pr-3">{{ row.name }}</td>
                  <td class="py-2 pr-3">{{ row.company_name || "" }}</td>
                  <td class="py-2">{{ row.is_default ? "Yes" : "" }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <form class="mt-4 space-y-3" @submit.prevent="savePayer">
            <select v-model="payerEditor.company_id" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit">
              <option :value="null">No linked company</option>
              <option v-for="row in companies" :key="row.id" :value="row.id">{{ row.name }}</option>
            </select>
            <input v-model="payerEditor.name" type="text" placeholder="Payer name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="payerEditor.tax_id" type="text" placeholder="Tax ID" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="payerEditor.address_line1" type="text" placeholder="Address line 1" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="payerEditor.address_line2" type="text" placeholder="Address line 2" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <div class="grid gap-3 sm:grid-cols-3">
              <input v-model="payerEditor.city" type="text" placeholder="City" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payerEditor.state" type="text" placeholder="State" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payerEditor.zip_code" type="text" placeholder="Zip code" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="payerEditor.email" type="email" placeholder="Email" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payerEditor.phone" type="text" placeholder="Phone" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <label class="inline-flex items-center gap-2 text-xs text-slate-300">
              <input v-model="payerEditor.is_default" type="checkbox" :disabled="!canEdit" />
              Set as default payer
            </label>
            <div class="flex gap-2">
              <button class="rounded-md bg-indigo-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700" :disabled="!canEdit || savingPayer">
                {{ savingPayer ? "Saving..." : payerEditor.id ? "Update Payer" : "Create Payer" }}
              </button>
              <button type="button" class="rounded-md border border-rose-700 px-4 py-2 text-xs font-semibold text-rose-300 hover:border-rose-500 disabled:cursor-not-allowed disabled:text-slate-500" :disabled="!canEdit || !payerEditor.id" @click="deletePayer">
                Delete
              </button>
            </div>
          </form>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-semibold text-white">Payee Profiles</h2>
            <p class="mt-1 text-xs text-slate-400">Editable payee records that drive payment matching and 480.6SP readiness.</p>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="search" type="text" placeholder="Search payee or tax ID" class="w-60 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" />
            <button class="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:border-slate-500" @click="resetPayeeEditor">New Payee</button>
          </div>
        </div>

        <div class="mt-4 grid gap-6 lg:grid-cols-[1fr_360px]">
          <div class="max-h-[720px] overflow-auto">
            <table class="min-w-full text-left text-xs">
              <thead class="text-slate-400">
                <tr>
                  <th class="pb-2 pr-3">Name</th>
                  <th class="pb-2 pr-3">Tax ID</th>
                  <th class="pb-2 pr-3">City</th>
                  <th class="pb-2">Type</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in payees" :key="row.id" class="cursor-pointer border-t border-slate-800 text-slate-200 hover:bg-slate-800/40" @click="editPayee(row)">
                  <td class="py-2 pr-3">{{ row.name }}</td>
                  <td class="py-2 pr-3">{{ row.tax_id || "" }}</td>
                  <td class="py-2 pr-3">{{ row.city || "" }}</td>
                  <td class="py-2">{{ row.payee_type || "" }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <form class="space-y-3" @submit.prevent="savePayee">
            <input v-model="payeeEditor.name" type="text" placeholder="Payee name" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="payeeEditor.tax_id" type="text" placeholder="Tax ID" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payeeEditor.payee_type" type="text" placeholder="Type" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <input v-model="payeeEditor.address_line1" type="text" placeholder="Address line 1" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <input v-model="payeeEditor.address_line2" type="text" placeholder="Address line 2" class="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            <div class="grid gap-3 sm:grid-cols-3">
              <input v-model="payeeEditor.city" type="text" placeholder="City" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payeeEditor.state" type="text" placeholder="State" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payeeEditor.zip_code" type="text" placeholder="Zip code" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <input v-model="payeeEditor.email" type="email" placeholder="Email" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
              <input v-model="payeeEditor.phone" type="text" placeholder="Phone" class="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs" :disabled="!canEdit" />
            </div>
            <div class="flex gap-2">
              <button class="rounded-md bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-900 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-700" :disabled="!canEdit || savingPayee">
                {{ savingPayee ? "Saving..." : payeeEditor.id ? "Update Payee" : "Create Payee" }}
              </button>
              <button type="button" class="rounded-md border border-rose-700 px-4 py-2 text-xs font-semibold text-rose-300 hover:border-rose-500 disabled:cursor-not-allowed disabled:text-slate-500" :disabled="!canEdit || !payeeEditor.id" @click="deletePayee">
                Delete
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { authHeaders, authState } from "../auth";

const API_BASE = "http://127.0.0.1:8000";

const canEdit = computed(() => authState.role === "admin" || authState.role === "operator");
const savingCompany = ref(false);
const savingPayer = ref(false);
const savingPayee = ref(false);
const seedingDemo = ref(false);
const search = ref("");
const companies = ref<any[]>([]);
const payers = ref<any[]>([]);
const payees = ref<any[]>([]);
const seedMessage = ref("");
const seedError = ref("");

const companyEditor = reactive<any>({
  id: null,
  name: "",
  legal_name: "",
  tax_id: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "PR",
  zip_code: "",
  email: "",
  phone: "",
  is_default: false,
});

const payerEditor = reactive<any>({
  id: null,
  company_id: null,
  name: "",
  tax_id: "",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "PR",
  zip_code: "",
  email: "",
  phone: "",
  is_default: false,
});

const payeeEditor = reactive<any>({
  id: null,
  name: "",
  tax_id: "",
  payee_type: "contractor",
  address_line1: "",
  address_line2: "",
  city: "",
  state: "PR",
  zip_code: "",
  email: "",
  phone: "",
});

const loadCompanies = async () => {
  const response = await fetch(`${API_BASE}/companies`);
  if (!response.ok) return;
  companies.value = await response.json();
};

const loadPayers = async () => {
  const response = await fetch(`${API_BASE}/profiles/payers`);
  if (!response.ok) return;
  payers.value = await response.json();
};

const loadPayees = async () => {
  const params = new URLSearchParams();
  if (search.value) params.append("search", search.value);
  const response = await fetch(`${API_BASE}/payments/payees?${params.toString()}`);
  if (!response.ok) return;
  payees.value = await response.json();
};

const seedDemoData = async () => {
  if (!canEdit.value) return;
  const confirmed = window.confirm("Load demo data for company, payer, payee, payments, and employee tables?");
  if (!confirmed) return;
  seedingDemo.value = true;
  seedMessage.value = "";
  seedError.value = "";
  try {
    const response = await fetch(`${API_BASE}/admin/seed-demo-data?replace_existing=true`, {
      method: "POST",
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      seedError.value = data.detail || "Unable to seed demo data.";
      return;
    }
    seedMessage.value = `Loaded demo data for ${data.companies_created} companies, ${data.payers_created} payers, ${data.payees_created} payees, and ${data.payment_records_created} payment records. Try 480.6SP Prep with ${data.recommended_payee_for_pdf}.`;
    await Promise.all([loadCompanies(), loadPayers(), loadPayees()]);
  } catch {
    seedError.value = "Failed to reach backend.";
  } finally {
    seedingDemo.value = false;
  }
};

const saveCompany = async () => {
  if (!canEdit.value) return;
  savingCompany.value = true;
  try {
    const method = companyEditor.id ? "PUT" : "POST";
    const url = companyEditor.id ? `${API_BASE}/companies/${companyEditor.id}` : `${API_BASE}/companies`;
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        name: companyEditor.name,
        legal_name: companyEditor.legal_name,
        tax_id: companyEditor.tax_id,
        address_line1: companyEditor.address_line1,
        address_line2: companyEditor.address_line2,
        city: companyEditor.city,
        state: companyEditor.state,
        zip_code: companyEditor.zip_code,
        email: companyEditor.email,
        phone: companyEditor.phone,
        is_default: companyEditor.is_default,
      }),
    });
    if (!response.ok) return;
    await Promise.all([loadCompanies(), loadPayers()]);
    resetCompanyEditor();
  } finally {
    savingCompany.value = false;
  }
};

const deleteCompany = async () => {
  if (!companyEditor.id || !canEdit.value) return;
  const confirmed = window.confirm("Delete this company profile?");
  if (!confirmed) return;
  await fetch(`${API_BASE}/companies/${companyEditor.id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await Promise.all([loadCompanies(), loadPayers()]);
  resetCompanyEditor();
};

const savePayer = async () => {
  if (!canEdit.value) return;
  savingPayer.value = true;
  try {
    const method = payerEditor.id ? "PUT" : "POST";
    const url = payerEditor.id ? `${API_BASE}/profiles/payers/${payerEditor.id}` : `${API_BASE}/profiles/payers`;
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        company_id: payerEditor.company_id,
        name: payerEditor.name,
        tax_id: payerEditor.tax_id,
        address_line1: payerEditor.address_line1,
        address_line2: payerEditor.address_line2,
        city: payerEditor.city,
        state: payerEditor.state,
        zip_code: payerEditor.zip_code,
        email: payerEditor.email,
        phone: payerEditor.phone,
        is_default: payerEditor.is_default,
      }),
    });
    if (!response.ok) return;
    await loadPayers();
    resetPayerEditor();
  } finally {
    savingPayer.value = false;
  }
};

const deletePayer = async () => {
  if (!payerEditor.id || !canEdit.value) return;
  const confirmed = window.confirm("Delete this payer profile?");
  if (!confirmed) return;
  await fetch(`${API_BASE}/profiles/payers/${payerEditor.id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await loadPayers();
  resetPayerEditor();
};

const savePayee = async () => {
  if (!canEdit.value) return;
  savingPayee.value = true;
  try {
    const method = payeeEditor.id ? "PUT" : "POST";
    const url = payeeEditor.id ? `${API_BASE}/payments/payees/${payeeEditor.id}` : `${API_BASE}/payments/payees`;
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({
        name: payeeEditor.name,
        tax_id: payeeEditor.tax_id,
        payee_type: payeeEditor.payee_type,
        address_line1: payeeEditor.address_line1,
        address_line2: payeeEditor.address_line2,
        city: payeeEditor.city,
        state: payeeEditor.state,
        zip_code: payeeEditor.zip_code,
        email: payeeEditor.email,
        phone: payeeEditor.phone,
      }),
    });
    if (!response.ok) return;
    await loadPayees();
    resetPayeeEditor();
  } finally {
    savingPayee.value = false;
  }
};

const deletePayee = async () => {
  if (!payeeEditor.id || !canEdit.value) return;
  const confirmed = window.confirm("Delete this payee profile?");
  if (!confirmed) return;
  const response = await fetch(`${API_BASE}/payments/payees/${payeeEditor.id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) return;
  await loadPayees();
  resetPayeeEditor();
};

const editCompany = (row: any) => Object.assign(companyEditor, row);
const editPayer = (row: any) => Object.assign(payerEditor, row);
const editPayee = (row: any) => Object.assign(payeeEditor, row);

const resetCompanyEditor = () =>
  Object.assign(companyEditor, {
    id: null,
    name: "",
    legal_name: "",
    tax_id: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "PR",
    zip_code: "",
    email: "",
    phone: "",
    is_default: false,
  });

const resetPayerEditor = () =>
  Object.assign(payerEditor, {
    id: null,
    company_id: null,
    name: "",
    tax_id: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "PR",
    zip_code: "",
    email: "",
    phone: "",
    is_default: false,
  });

const resetPayeeEditor = () =>
  Object.assign(payeeEditor, {
    id: null,
    name: "",
    tax_id: "",
    payee_type: "contractor",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "PR",
    zip_code: "",
    email: "",
    phone: "",
  });

watch(search, () => {
  loadPayees();
});

onMounted(async () => {
  await Promise.all([loadCompanies(), loadPayers(), loadPayees()]);
});
</script>
