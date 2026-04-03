<template>
  <div v-if="isPublicPage" class="min-h-screen bg-slate-950 text-slate-100">
    <router-view />
  </div>
  <div v-else class="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(8,145,178,0.14),_transparent_22%),radial-gradient(circle_at_bottom_left,_rgba(245,158,11,0.12),_transparent_24%),#020617] text-slate-100">
    <div class="grid min-h-screen lg:grid-cols-[260px_1fr]">
      <aside class="border-r border-slate-800/80 bg-slate-950/75 px-5 py-6 backdrop-blur">
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.32em] text-cyan-300/75">Las Vegas Corp</p>
          <h1 class="mt-3 text-2xl font-semibold tracking-tight text-white">Operations Hub</h1>
          <p class="mt-2 text-sm leading-6 text-slate-400">
            Daily employee records, imports, analytics, and report tools in one workspace.
          </p>
        </div>

        <div class="mt-8 space-y-6">
          <section>
            <div class="px-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">Overview</div>
            <div class="mt-3 space-y-1">
              <router-link
                to="/"
                class="flex rounded-2xl px-3 py-2.5 text-sm transition"
                :class="linkClass('/')"
              >
                Dashboard
              </router-link>
              <router-link
                to="/preferences"
                class="flex rounded-2xl px-3 py-2.5 text-sm transition"
                :class="linkClass('/preferences')"
              >
                Preferences
              </router-link>
            </div>
          </section>

          <section v-if="canSeeTools">
            <div class="px-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">Tools</div>
            <div class="mt-3 space-y-1">
              <router-link to="/tools" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/tools')">Tools Home</router-link>
            </div>
          </section>

          <section>
            <div class="px-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">Workspace</div>
            <div class="mt-3 space-y-1">
              <router-link v-if="canManageImports" to="/imports" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/imports')">Imports</router-link>
              <router-link to="/employees" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/employees')">Employees</router-link>
              <router-link to="/records" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/records')">Records</router-link>
              <router-link to="/payments" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/payments')">Payments</router-link>
              <router-link to="/payment-profiles" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/payment-profiles')">Payment Profiles</router-link>
            </div>
          </section>

          <section v-if="canSeeTools">
            <div class="px-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">Report Tools</div>
            <div class="mt-3 space-y-1">
              <router-link to="/payroll" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/payroll')">Employee Classifier</router-link>
              <router-link to="/payroll-summary" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/payroll-summary')">Payroll Summary Extractor</router-link>
              <router-link to="/form-480-prep" class="flex rounded-2xl px-3 py-2.5 text-sm transition" :class="linkClass('/form-480-prep')">Form 480 Prep</router-link>
            </div>
          </section>
        </div>

        <div class="mt-10 rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
          <div class="text-sm font-semibold text-white">{{ authState.userName }}</div>
          <div class="mt-1 text-xs text-slate-400">{{ authState.email }}</div>
          <div class="mt-3 inline-flex rounded-full border border-slate-800 bg-slate-950/90 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-cyan-200">
            {{ authState.role }}
          </div>
          <button
            class="mt-4 w-full rounded-xl border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
            @click="signOut"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div>
        <header class="border-b border-slate-800/80 bg-slate-950/40 px-6 py-5 backdrop-blur">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">{{ currentSection }}</p>
              <h2 class="mt-2 text-2xl font-semibold tracking-tight text-white">{{ currentTitle }}</h2>
            </div>
            <div class="rounded-full border border-slate-800 bg-slate-950/70 px-4 py-2 text-xs text-slate-300">
              Local desktop session
            </div>
          </div>
        </header>

        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authState, hasRoleAccess, logout } from "./auth";

const route = useRoute();
const router = useRouter();

const isPublicPage = computed(() => Boolean(route.meta.public));

const titleMap: Record<string, string> = {
  login: "Login",
  landing: "Dashboard",
  preferences: "Preferences",
  tools: "Tools Center",
  imports: "Imports Workspace",
  employees: "Employees Workspace",
  records: "Records Workspace",
  payments: "Payments Workspace",
  "payment-profiles": "Payment Profiles",
  payroll: "Employee Classifier Tool",
  "payroll-summary": "Payroll Summary Extractor",
  "form-480-prep": "Form 480.6SP Prep",
};

const sectionMap: Record<string, string> = {
  login: "Access",
  landing: "Overview",
  preferences: "Preferences",
  tools: "Tools",
  imports: "Workspace",
  employees: "Workspace",
  records: "Workspace",
  payments: "Workspace",
  "payment-profiles": "Workspace",
  payroll: "Report Tools",
  "payroll-summary": "Report Tools",
  "form-480-prep": "Report Tools",
};

const currentTitle = computed(() => titleMap[String(route.name || "")] || "Workspace");
const currentSection = computed(() => sectionMap[String(route.name || "")] || "Workspace");
const canSeeTools = computed(() => hasRoleAccess(["admin", "operator"]));
const canManageImports = computed(() => hasRoleAccess(["admin", "operator"]));

const linkClass = (path: string) =>
  route.path === path
    ? "bg-cyan-400/15 text-cyan-200 ring-1 ring-cyan-400/30"
    : "text-slate-300 hover:bg-slate-900/70 hover:text-white";

const signOut = async () => {
  logout();
  await router.push("/login");
};
</script>
