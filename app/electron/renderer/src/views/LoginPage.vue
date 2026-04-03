<template>
  <main class="login-screen min-h-screen px-6 py-10 text-slate-100">
    <div class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.1fr_480px]">
      <section class="rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.25),_transparent_35%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(2,6,23,0.98))] p-8 shadow-2xl shadow-slate-950/50">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/80">Las Vegas Corp</p>
        <h1 class="mt-5 max-w-xl text-4xl font-semibold leading-tight tracking-tight text-white">
          Daily employee operations, reporting, and data history in one workspace.
        </h1>
        <p class="mt-4 max-w-2xl text-sm leading-6 text-slate-300">
          Use one application to ingest spreadsheets, classify employees, search records, and generate Puerto Rico-focused reports without juggling separate files.
        </p>

        <div class="mt-8 grid gap-4 sm:grid-cols-3">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Imports</div>
            <div class="mt-2 text-sm text-slate-200">Structured ingestion for payroll summary sections and employee records.</div>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Employees</div>
            <div class="mt-2 text-sm text-slate-200">Search by name, review tasks, dates, patients, and running totals.</div>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Reports</div>
            <div class="mt-2 text-sm text-slate-200">Generate classifier and payroll summary outputs from one place.</div>
          </div>
        </div>
      </section>

      <section class="rounded-[28px] border border-slate-800 bg-slate-950/90 p-8 shadow-2xl shadow-slate-950/50">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.25em] text-amber-300/80">Workspace Login</p>
            <h2 class="mt-3 text-2xl font-semibold text-white">Sign in</h2>
          </div>
          <div class="rounded-full border border-slate-800 px-3 py-1 text-[11px] text-slate-400">Local session</div>
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="submitLogin">
          <div>
            <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Role</label>
            <select
              v-model="role"
              class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
            >
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          <div>
            <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Email</label>
            <input
              v-model="email"
              type="email"
              autocomplete="email"
              class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Password</label>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
              placeholder="Enter your password"
            />
          </div>

          <div v-if="errorMessage" class="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            class="w-full rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Enter Workspace
          </button>
        </form>

        <div class="mt-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-xs text-slate-400">
          This login is a local session shell for the desktop app. We can wire real authentication next once we decide on local-only accounts or cloud-backed users.
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { login, type UserRole } from "../auth";

const router = useRouter();

const role = ref<UserRole>("operator");
const email = ref("");
const password = ref("");
const errorMessage = ref("");

const submitLogin = async () => {
  errorMessage.value = "";
  try {
    login(email.value, password.value, role.value);
    await router.push("/");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to sign in.";
  }
};
</script>
