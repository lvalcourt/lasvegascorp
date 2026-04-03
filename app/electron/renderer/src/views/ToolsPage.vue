<template>
  <main class="px-8 py-10">
    <section class="rounded-[28px] border border-slate-800 bg-[linear-gradient(135deg,rgba(15,23,42,0.95),rgba(2,6,23,0.98))] p-8 shadow-2xl shadow-slate-950/40">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/75">Tool Center</p>
          <h2 class="mt-3 text-3xl font-semibold tracking-tight text-white">Run reporting workflows from one place.</h2>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Use the two core report tools for validation, classification, and payroll-summary extraction. This page gives operators a clear starting point without hunting through the workspace.
          </p>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-xs text-slate-300">
          <div class="text-slate-500">Default mileage multiplier</div>
          <div class="mt-1 text-lg font-semibold text-white">{{ mileagePreference.toFixed(2) }}</div>
        </div>
      </div>

      <div class="mt-8 grid gap-6 lg:grid-cols-2">
        <article class="rounded-3xl border border-slate-800 bg-slate-950/75 p-6">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-amber-300">Tax Prep</p>
            <span class="rounded-full border border-amber-400/25 bg-amber-400/10 px-3 py-1 text-[11px] text-amber-200">Payments + readiness</span>
          </div>
          <h3 class="mt-4 text-2xl font-semibold text-white">Form 480.6SP Prep</h3>
          <p class="mt-3 text-sm leading-6 text-slate-400">
            Review services-rendered totals by year, identify missing tax IDs, and prepare the data packet we’ll later map into the official 480.6SP filing form.
          </p>
          <ul class="mt-5 space-y-2 text-sm text-slate-300">
            <li>Summarizes payees and yearly totals.</li>
            <li>Flags missing tax IDs early.</li>
            <li>Pairs naturally with the Payments workspace.</li>
          </ul>
          <router-link
            to="/form-480-prep"
            class="mt-6 inline-flex items-center rounded-2xl bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
          >
            Open 480.6SP Prep
          </router-link>
        </article>

        <article class="rounded-3xl border border-slate-800 bg-slate-950/75 p-6">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-300">Validation Tool</p>
            <span class="rounded-full border border-indigo-400/25 bg-indigo-400/10 px-3 py-1 text-[11px] text-indigo-200">Rules + output sheets</span>
          </div>
          <h3 class="mt-4 text-2xl font-semibold text-white">Employee Classifier Tool</h3>
          <p class="mt-3 text-sm leading-6 text-slate-400">
            Validate spreadsheet structure, apply editable rules, classify employees, and export operational report sheets like discipline and completion checks.
          </p>
          <ul class="mt-5 space-y-2 text-sm text-slate-300">
            <li>Editable rule library saved locally.</li>
            <li>Discipline and completion report filters.</li>
            <li>Employee and row-level validation statistics.</li>
          </ul>
          <router-link
            to="/payroll"
            class="mt-6 inline-flex items-center rounded-2xl bg-indigo-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-indigo-300"
          >
            Open Employee Classifier
          </router-link>
        </article>

        <article class="rounded-3xl border border-slate-800 bg-slate-950/75 p-6">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-300">Section Reader</p>
            <span class="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-[11px] text-emerald-200">Payroll Summary format</span>
          </div>
          <h3 class="mt-4 text-2xl font-semibold text-white">Payroll Summary Extractor</h3>
          <p class="mt-3 text-sm leading-6 text-slate-400">
            Read employee sections that begin with Payroll Summary, identify employee type from task tokens, and build exportable totals by employee.
          </p>
          <ul class="mt-5 space-y-2 text-sm text-slate-300">
            <li>Parses section-based payroll exports.</li>
            <li>Retains employee date and patient-level records.</li>
            <li>Creates Terapia and Enfermeria rollups.</li>
          </ul>
          <router-link
            to="/payroll-summary"
            class="mt-6 inline-flex items-center rounded-2xl bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300"
          >
            Open Payroll Summary Extractor
          </router-link>
        </article>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { preferencesState } from "../preferences";

const mileagePreference = computed(() => Number(preferencesState.defaultMileageMultiplier || 1));
</script>
