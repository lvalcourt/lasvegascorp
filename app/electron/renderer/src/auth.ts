import { reactive } from "vue";

export type UserRole = "admin" | "operator" | "viewer";
const API_BASE = "http://127.0.0.1:8000";

type AuthState = {
  loggedIn: boolean;
  userName: string;
  email: string;
  role: UserRole;
  token: string;
  mustChangePassword: boolean;
};

const AUTH_STORAGE_KEY = "lvc-auth-session";
const hasSecureDesktopAuth = () => typeof window !== "undefined" && Boolean(window.api?.auth);

async function loadPersistedSession() {
  if (hasSecureDesktopAuth()) {
    const raw = await window.api!.auth!.getSession();
    return raw ? JSON.parse(raw) : null;
  }
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function savePersistedSession(payload: unknown) {
  const raw = JSON.stringify(payload);
  if (hasSecureDesktopAuth()) {
    await window.api!.auth!.setSession(raw);
    return;
  }
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_STORAGE_KEY, raw);
  }
}

async function clearPersistedSession() {
  if (hasSecureDesktopAuth()) {
    await window.api!.auth!.clearSession();
    return;
  }
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

const savedSession = (() => {
  if (typeof window === "undefined" || hasSecureDesktopAuth()) {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

export const authState = reactive<AuthState>({
  loggedIn: Boolean(savedSession?.loggedIn && savedSession?.token),
  userName: savedSession?.userName || "",
  email: savedSession?.email || "",
  role: savedSession?.role || "operator",
  token: savedSession?.token || "",
  mustChangePassword: Boolean(savedSession?.mustChangePassword),
});

function persist() {
  void savePersistedSession(authState);
}

export async function login(email: string, password: string) {
  if (!email.trim() || !password.trim()) {
    throw new Error("Email and password are required.");
  }

  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: email.trim(),
      password,
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Unable to sign in.");
  }

  authState.loggedIn = true;
  authState.email = payload.email || email.trim();
  authState.userName = payload.display_name || email.split("@")[0] || "User";
  authState.role = payload.role || "operator";
  authState.token = payload.token || "";
  authState.mustChangePassword = Boolean(payload.must_change_password);
  persist();
}

export async function logout() {
  if (authState.token) {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: authHeaders(),
    }).catch(() => undefined);
  }
  authState.loggedIn = false;
  authState.userName = "";
  authState.email = "";
  authState.role = "operator";
  authState.token = "";
  authState.mustChangePassword = false;
  await clearPersistedSession();
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const response = await fetch(`${API_BASE}/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Unable to change password.");
  }
  authState.mustChangePassword = false;
  persist();
}

export async function hydrateSession() {
  const persisted = await loadPersistedSession();
  if (persisted) {
    authState.loggedIn = Boolean(persisted.loggedIn && persisted.token);
    authState.email = persisted.email || "";
    authState.userName = persisted.userName || "";
    authState.role = persisted.role || "operator";
    authState.token = persisted.token || "";
    authState.mustChangePassword = Boolean(persisted.mustChangePassword);
  }
  if (!authState.token) {
    return;
  }
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: authHeaders(),
  }).catch(() => null);
  if (!response || !response.ok) {
    await logout();
    return;
  }
  const payload = await response.json().catch(() => null);
  if (!payload) {
    await logout();
    return;
  }
  authState.loggedIn = true;
  authState.email = payload.email || authState.email;
  authState.userName = payload.display_name || authState.userName;
  authState.role = payload.role || authState.role;
  authState.mustChangePassword = Boolean(payload.must_change_password);
  persist();
}

export function hasRoleAccess(allowedRoles?: UserRole[]) {
  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }
  return allowedRoles.includes(authState.role);
}

export function authHeaders() {
  return {
    "x-auth-token": authState.token,
  };
}
