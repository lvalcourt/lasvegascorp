<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <header class="border-b border-slate-800 px-8 py-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Las Vegas Corp</h1>
          <p class="text-slate-400">Automation suite for employee classification and reporting.</p>
        </div>
        <router-link to="/" class="text-xs font-semibold text-slate-300 hover:text-slate-100">
          Home
        </router-link>
      </div>
    </header>

    <router-view />
  </div>
</template>
