<template>
  <main class="login-screen tp-shell min-h-screen px-6 py-10 text-slate-100">
    <div class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.1fr_480px]">
      <section class="tp-glass rounded-[28px] bg-[radial-gradient(circle_at_top_left,_rgba(103,232,249,0.18),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(167,139,250,0.16),_transparent_26%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(2,6,23,0.98))] p-8">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/80">TrakinPR</p>
        <div class="mt-5 overflow-hidden rounded-[28px] border border-cyan-400/15 bg-slate-950/40 p-3">
          <img :src="trakinLogo" alt="TrakinPR logo" class="w-full rounded-[22px]" />
        </div>
        <h1 class="mt-5 max-w-xl text-4xl font-semibold leading-tight tracking-tight text-white">
          Daily operations, reporting, and business history in one workspace.
        </h1>
        <p class="mt-3 text-sm font-semibold uppercase tracking-[0.26em] text-cyan-200/90">
          Accountability, fast tracking, and automated financial deployment.
        </p>
        <p class="mt-4 max-w-2xl text-sm leading-6 text-slate-300">
          Use one application to ingest spreadsheets, track documents and spending, search records, and manage Puerto Rico-focused compliance workflows without juggling separate files.
        </p>

        <div class="mt-8 grid gap-4 sm:grid-cols-3">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Imports</div>
            <div class="mt-2 text-sm text-slate-200">Structured ingestion for payroll summaries, receipts, payments, and business records.</div>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Employees</div>
            <div class="mt-2 text-sm text-slate-200">Search by name, review activity, dates, patients, and running totals.</div>
          </div>
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div class="text-xs uppercase tracking-[0.25em] text-slate-400">Reports</div>
            <div class="mt-2 text-sm text-slate-200">Generate classifier, payroll summary, and compliance outputs from one place.</div>
          </div>
        </div>

        <footer class="mt-8 flex flex-col gap-3 border-t border-white/10 pt-5 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="font-semibold tracking-[0.22em] text-slate-300">TRAKINPR</div>
            <div class="mt-1">Accountability, fast tracking, and automated financial deployment.</div>
          </div>
          <div class="text-slate-500">
            Built for document-heavy workflows across small business operations.
          </div>
        </footer>
      </section>

      <section class="tp-panel rounded-[28px] p-8">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.25em] text-amber-300/80">Workspace Login</p>
            <h2 class="mt-3 text-2xl font-semibold text-white">Sign in</h2>
          </div>
          <div class="rounded-full border border-cyan-400/15 px-3 py-1 text-[11px] text-slate-400">Local accounts</div>
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="submitLogin">
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
            class="w-full rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 shadow-[0_0_30px_-12px_rgba(34,211,238,0.65)] transition hover:bg-cyan-300"
          >
            Enter Workspace
          </button>
        </form>

        <div class="tp-panel-soft mt-8 rounded-2xl p-4 text-xs text-slate-400">
          Admins can now create and manage local workspace accounts for operators and viewers.
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { login } from "../auth";
import trakinLogo from "../assets/trakinpr-logo.svg";

const router = useRouter();

const email = ref("");
const password = ref("");
const errorMessage = ref("");

const submitLogin = async () => {
  errorMessage.value = "";
  try {
    await login(email.value, password.value);
    await router.push("/");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to sign in.";
  }
};
</script>
