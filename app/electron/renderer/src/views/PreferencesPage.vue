<template>
  <main class="px-8 py-10">
    <section class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <div class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8 shadow-2xl shadow-slate-950/40">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/75">Preferences</p>
        <h2 class="mt-4 text-3xl font-semibold tracking-tight text-white">Set your working defaults.</h2>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          These settings stay local to this desktop session and are reused across imports, employee views, tools, and dashboard analytics.
        </p>

        <div class="mt-8 grid gap-6 lg:grid-cols-2">
          <div class="rounded-3xl border border-slate-800 bg-slate-950/75 p-5">
            <label class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Default Mileage Multiplier</label>
            <input
              v-model.number="mileagePreference"
              type="number"
              step="0.01"
              min="0"
              class="mt-3 w-full rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
            />
            <p class="mt-3 text-xs leading-5 text-slate-400">
              Used as the starting value in Imports, Employees, Employee Classifier, and Payroll Summary Extractor.
            </p>
          </div>

          <div class="rounded-3xl border border-slate-800 bg-slate-950/75 p-5">
            <label class="flex items-start gap-3">
              <input v-model="dashboardIncludeHistory" type="checkbox" class="mt-1" />
              <span>
                <span class="block text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Dashboard Includes History</span>
                <span class="mt-3 block text-sm leading-6 text-slate-300">
                  When enabled, the dashboard charts include inactive historical records from previous imports.
                </span>
              </span>
            </label>
          </div>
        </div>

        <div class="mt-6 rounded-3xl border border-slate-800 bg-slate-950/75 p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Password & Security</label>
              <p class="mt-3 text-sm leading-6 text-slate-400">
                Use a stronger password with at least 8 characters, one uppercase letter, one lowercase letter, and one number.
              </p>
            </div>
            <div v-if="authState.mustChangePassword" class="rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-200">
              Password update required
            </div>
          </div>

          <form class="mt-5 grid gap-4 lg:grid-cols-3" @submit.prevent="submitPasswordChange">
            <input
              v-model="currentPassword"
              type="password"
              placeholder="Current password"
              class="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
            />
            <input
              v-model="newPassword"
              type="password"
              placeholder="New password"
              class="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400"
            />
            <button type="submit" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300">
              Update Password
            </button>
          </form>
          <div v-if="passwordMessage" class="mt-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
            {{ passwordMessage }}
          </div>
          <div v-if="passwordError" class="mt-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {{ passwordError }}
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <section class="rounded-[28px] border border-slate-800 bg-slate-900/70 p-6">
          <h3 class="text-lg font-semibold text-white">Current Session</h3>
          <div class="mt-5 grid gap-3 text-sm text-slate-300">
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-slate-500">User</div>
              <div class="mt-2 font-semibold text-white">{{ authState.userName }}</div>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Email</div>
              <div class="mt-2 text-white">{{ authState.email || "Not set" }}</div>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <div class="text-xs uppercase tracking-[0.22em] text-slate-500">Role</div>
              <div class="mt-2 inline-flex rounded-full border border-cyan-400/25 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">
                {{ authState.role }}
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-[28px] border border-slate-800 bg-slate-900/70 p-6">
          <h3 class="text-lg font-semibold text-white">Where Defaults Apply</h3>
          <ul class="mt-4 space-y-3 text-sm leading-6 text-slate-300">
            <li>Dashboard analytics refreshes with your saved history preference.</li>
            <li>Imports starts with your saved mileage multiplier.</li>
            <li>Employee tables keep raw mileage and show the derived multiplied total.</li>
            <li>Both report tools start from the same saved multiplier.</li>
          </ul>
        </section>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import { authState, changePassword } from "../auth";
import { preferencesState, setDashboardIncludeHistory, useMileagePreference } from "../preferences";

const mileagePreference = useMileagePreference();
const currentPassword = ref("");
const newPassword = ref("");
const passwordMessage = ref("");
const passwordError = ref("");
const dashboardIncludeHistory = computed({
  get: () => preferencesState.dashboardIncludeHistory,
  set: (value: boolean) => {
    setDashboardIncludeHistory(value);
  },
});

const submitPasswordChange = async () => {
  passwordMessage.value = "";
  passwordError.value = "";
  try {
    await changePassword(currentPassword.value, newPassword.value);
    currentPassword.value = "";
    newPassword.value = "";
    passwordMessage.value = "Password updated successfully.";
  } catch (error) {
    passwordError.value = error instanceof Error ? error.message : "Unable to update password.";
  }
};
</script>
