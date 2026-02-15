<template>
  <main class="px-8 py-12">
    <div class="mx-auto max-w-4xl">
      <div class="grid gap-6 sm:grid-cols-2">
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
    </div>
  </main>
</template>
