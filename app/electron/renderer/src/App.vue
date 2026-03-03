<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <header class="border-b border-slate-800 px-8 py-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Las Vegas Corp</h1>
          <p class="text-slate-400">Automation suite for employee classification and reporting.</p>
        </div>
        <nav class="flex items-center gap-4 text-xs font-semibold text-slate-300">
          <router-link to="/" class="hover:text-slate-100">Home</router-link>
          <router-link to="/imports" class="hover:text-slate-100">Imports</router-link>
          <router-link to="/employees" class="hover:text-slate-100">Employees</router-link>
          <router-link to="/records" class="hover:text-slate-100">Records</router-link>
          <router-link to="/payroll" class="hover:text-slate-100">Reports</router-link>
        </nav>
      </div>
    </header>

    <router-view />
  </div>
</template>
