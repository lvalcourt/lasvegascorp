import { reactive } from "vue";

export type UserRole = "admin" | "operator" | "viewer";

type AuthState = {
  loggedIn: boolean;
  userName: string;
  email: string;
  role: UserRole;
};

const AUTH_STORAGE_KEY = "lvc-auth-session";

const savedSession = (() => {
  if (typeof window === "undefined") {
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
  loggedIn: Boolean(savedSession?.loggedIn),
  userName: savedSession?.userName || "",
  email: savedSession?.email || "",
  role: savedSession?.role || "operator",
});

function persist() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authState));
}

export function login(email: string, password: string, role: UserRole = "operator") {
  if (!email.trim() || !password.trim()) {
    throw new Error("Email and password are required.");
  }

  authState.loggedIn = true;
  authState.email = email.trim();
  authState.userName = email.split("@")[0] || "User";
  authState.role = role;
  persist();
}

export function logout() {
  authState.loggedIn = false;
  authState.userName = "";
  authState.email = "";
  authState.role = "operator";
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

export function hasRoleAccess(allowedRoles?: UserRole[]) {
  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }
  return allowedRoles.includes(authState.role);
}

export function authHeaders() {
  return {
    "x-user-role": authState.role,
    "x-user-email": authState.email,
  };
}
