<template>
  <main class="px-8 py-10">
    <section class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div class="rounded-[28px] border border-slate-800 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(2,6,23,0.98))] p-8 shadow-2xl shadow-slate-950/40">
        <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300/75">Admin</p>
        <h2 class="mt-4 text-3xl font-semibold tracking-tight text-white">Workspace Accounts</h2>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          Create and manage local accounts for admins, operators, and viewers so access is handled from one place.
        </p>

        <form class="mt-8 space-y-5" @submit.prevent="saveUser">
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Display Name</label>
              <input v-model="form.display_name" class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400" />
            </div>
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Email</label>
              <input v-model="form.email" type="email" class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400" :disabled="Boolean(editingId)" />
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Role</label>
              <select v-model="form.role" class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400">
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <label class="flex items-center gap-3 pt-8 text-sm text-slate-300">
              <input v-model="form.is_active" type="checkbox" />
              Active account
            </label>
          </div>

          <label class="flex items-center gap-3 text-sm text-slate-300">
            <input v-model="form.must_change_password" type="checkbox" />
            Require password change at next login
          </label>

          <div>
            <label class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
              {{ editingId ? "New Password (Optional)" : "Password" }}
            </label>
            <input v-model="form.password" type="password" class="mt-2 w-full rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400" />
          </div>

          <div v-if="message" class="rounded-2xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
            {{ message }}
          </div>
          <div v-if="errorMessage" class="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {{ errorMessage }}
          </div>

          <div class="flex flex-wrap gap-3">
            <button type="submit" class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300">
              {{ editingId ? "Update Account" : "Create Account" }}
            </button>
            <button v-if="editingId" type="button" class="rounded-2xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500" @click="resetForm">
              Cancel
            </button>
          </div>
        </form>
      </div>

      <section class="space-y-6">
        <div class="rounded-[28px] border border-slate-800 bg-slate-900/70 p-6">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-white">Existing Accounts</h3>
            <p class="mt-1 text-sm text-slate-400">These users can sign in from the local login page.</p>
          </div>
          <div class="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">{{ users.length }} accounts</div>
        </div>

        <div class="mt-5 overflow-hidden rounded-3xl border border-slate-800">
          <table class="min-w-full divide-y divide-slate-800 text-sm">
            <thead class="bg-slate-950/80 text-left text-xs uppercase tracking-[0.2em] text-slate-500">
              <tr>
                <th class="px-4 py-3">User</th>
                <th class="px-4 py-3">Role</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800 bg-slate-950/35 text-slate-200">
              <tr v-for="user in users" :key="user.id">
                <td class="px-4 py-3">
                  <div class="font-semibold text-white">{{ user.display_name }}</div>
                  <div class="mt-1 text-xs text-slate-400">{{ user.email }}</div>
                  <div v-if="user.must_change_password" class="mt-2 text-[11px] uppercase tracking-[0.18em] text-amber-300">Password reset pending</div>
                </td>
                <td class="px-4 py-3">{{ user.role }}</td>
                <td class="px-4 py-3">
                  <span class="rounded-full px-2 py-1 text-xs" :class="user.is_active ? 'bg-emerald-500/10 text-emerald-200' : 'bg-slate-800 text-slate-300'">
                    {{ user.is_active ? "Active" : "Inactive" }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap gap-2">
                    <button class="rounded-xl border border-slate-700 px-3 py-2 text-xs text-slate-200 transition hover:border-cyan-400/40" @click="editUser(user)">Edit</button>
                    <button class="rounded-xl border border-rose-500/30 px-3 py-2 text-xs text-rose-200 transition hover:border-rose-400/50" :disabled="user.email === authState.email" @click="deleteUser(user)">
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="4" class="px-4 py-6 text-center text-slate-500">No accounts yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
        </div>

        <div class="rounded-[28px] border border-slate-800 bg-slate-900/70 p-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-white">Recent Security Activity</h3>
              <p class="mt-1 text-sm text-slate-400">A small audit trail for account changes and sign-ins.</p>
            </div>
          </div>
          <div class="mt-5 space-y-3">
            <div v-for="item in auditRows" :key="item.id" class="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
              <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
                <div class="font-semibold text-white">{{ item.action }}</div>
                <div class="text-xs text-slate-500">{{ item.created_at }}</div>
              </div>
              <div class="mt-2 text-sm text-slate-300">{{ item.detail || "No detail provided." }}</div>
              <div class="mt-2 text-xs text-slate-500">User: {{ item.user_email || "n/a" }} · Actor: {{ item.actor_email || "system" }}</div>
            </div>
            <div v-if="!auditRows.length" class="rounded-2xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-500">
              No activity yet.
            </div>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import { authHeaders, authState, type UserRole } from "../auth";

const API_BASE = "http://127.0.0.1:8000";

type UserRow = {
  id: number;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  must_change_password: boolean;
};
type AuditRow = {
  id: number;
  action: string;
  detail: string;
  created_at: string;
  user_email?: string;
  actor_email?: string;
};

const users = ref<UserRow[]>([]);
const auditRows = ref<AuditRow[]>([]);
const editingId = ref<number | null>(null);
const message = ref("");
const errorMessage = ref("");
const form = reactive({
  email: "",
  display_name: "",
  role: "viewer" as UserRole,
  password: "",
  is_active: true,
  must_change_password: true,
});

const resetForm = () => {
  editingId.value = null;
  form.email = "";
  form.display_name = "";
  form.role = "viewer";
  form.password = "";
  form.is_active = true;
  form.must_change_password = true;
};

const loadUsers = async () => {
  const response = await fetch(`${API_BASE}/admin/users`, {
    headers: authHeaders(),
  });
  if (!response.ok) return;
  users.value = await response.json();
};

const loadAudit = async () => {
  const response = await fetch(`${API_BASE}/admin/users/audit`, {
    headers: authHeaders(),
  });
  if (!response.ok) return;
  auditRows.value = await response.json();
};

const saveUser = async () => {
  errorMessage.value = "";
  message.value = "";
  const payload = {
    email: form.email,
    display_name: form.display_name,
    role: form.role,
    password: form.password || undefined,
    is_active: form.is_active,
    must_change_password: form.must_change_password,
  };
  const url = editingId.value ? `${API_BASE}/admin/users/${editingId.value}` : `${API_BASE}/admin/users`;
  const method = editingId.value ? "PUT" : "POST";
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(editingId.value ? { display_name: payload.display_name, role: payload.role, password: payload.password, is_active: payload.is_active } : payload),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    errorMessage.value = result.detail || "Unable to save account.";
    return;
  }
  message.value = editingId.value ? "Account updated." : "Account created.";
  resetForm();
  await loadUsers();
  await loadAudit();
};

const editUser = (user: UserRow) => {
  editingId.value = user.id;
  form.email = user.email;
  form.display_name = user.display_name;
  form.role = user.role;
  form.password = "";
  form.is_active = user.is_active;
  form.must_change_password = user.must_change_password;
  errorMessage.value = "";
  message.value = "";
};

const deleteUser = async (user: UserRow) => {
  if (!window.confirm(`Delete account for ${user.display_name}?`)) return;
  const response = await fetch(`${API_BASE}/admin/users/${user.id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    errorMessage.value = result.detail || "Unable to delete account.";
    return;
  }
  message.value = "Account deleted.";
  await loadUsers();
  await loadAudit();
};

onMounted(async () => {
  await loadUsers();
  await loadAudit();
});
</script>
