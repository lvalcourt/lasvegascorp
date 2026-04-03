import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import { authState, hasRoleAccess, type UserRole } from "./auth";
import LandingPage from "./views/LandingPage.vue";
import LoginPage from "./views/LoginPage.vue";
import ImportsPage from "./views/ImportsPage.vue";
import EmployeesPage from "./views/EmployeesPage.vue";
import RecordsPage from "./views/RecordsPage.vue";
import PayrollTool from "./views/PayrollTool.vue";
import PayrollSummaryTool from "./views/PayrollSummaryTool.vue";
import ToolsPage from "./views/ToolsPage.vue";
import PreferencesPage from "./views/PreferencesPage.vue";
import PaymentsPage from "./views/PaymentsPage.vue";
import Form480PrepPage from "./views/Form480PrepPage.vue";
import PaymentProfilesPage from "./views/PaymentProfilesPage.vue";

type RouteMeta = {
  public?: boolean;
  requiresAuth?: boolean;
  section?: string;
  roles?: UserRole[];
};

const routes = [
  { path: "/login", name: "login", component: LoginPage, meta: { public: true } as RouteMeta },
  { path: "/", name: "landing", component: LandingPage, meta: { requiresAuth: true, section: "overview" } as RouteMeta },
  { path: "/preferences", name: "preferences", component: PreferencesPage, meta: { requiresAuth: true, section: "preferences" } as RouteMeta },
  { path: "/tools", name: "tools", component: ToolsPage, meta: { requiresAuth: true, section: "tools", roles: ["admin", "operator"] } as RouteMeta },
  { path: "/imports", name: "imports", component: ImportsPage, meta: { requiresAuth: true, section: "workspace", roles: ["admin", "operator"] } as RouteMeta },
  { path: "/employees", name: "employees", component: EmployeesPage, meta: { requiresAuth: true, section: "workspace" } as RouteMeta },
  { path: "/records", name: "records", component: RecordsPage, meta: { requiresAuth: true, section: "workspace" } as RouteMeta },
  { path: "/payments", name: "payments", component: PaymentsPage, meta: { requiresAuth: true, section: "workspace" } as RouteMeta },
  { path: "/payment-profiles", name: "payment-profiles", component: PaymentProfilesPage, meta: { requiresAuth: true, section: "workspace" } as RouteMeta },
  { path: "/form-480-prep", name: "form-480-prep", component: Form480PrepPage, meta: { requiresAuth: true, section: "reports" } as RouteMeta },
  { path: "/payroll", name: "payroll", component: PayrollTool, meta: { requiresAuth: true, section: "reports", roles: ["admin", "operator"] } as RouteMeta },
  { path: "/payroll-summary", name: "payroll-summary", component: PayrollSummaryTool, meta: { requiresAuth: true, section: "reports", roles: ["admin", "operator"] } as RouteMeta },
];

const useHashHistory = typeof window !== "undefined" && window.location.protocol === "file:";

const router = createRouter({
  history: useHashHistory ? createWebHashHistory() : createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.public) {
    if (authState.loggedIn && to.name === "login") {
      return { name: "landing" };
    }
    return true;
  }

  if (to.meta.requiresAuth && !authState.loggedIn) {
    return { name: "login" };
  }

  if (!hasRoleAccess(to.meta.roles as UserRole[] | undefined)) {
    return { name: "landing" };
  }

  return true;
});

export default router;
