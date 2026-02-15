import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import LandingPage from "./views/LandingPage.vue";
import PayrollTool from "./views/PayrollTool.vue";
import PayrollSummaryTool from "./views/PayrollSummaryTool.vue";

const routes = [
  { path: "/", name: "landing", component: LandingPage },
  { path: "/payroll", name: "payroll", component: PayrollTool },
  { path: "/payroll-summary", name: "payroll-summary", component: PayrollSummaryTool },
];

const useHashHistory = typeof window !== "undefined" && window.location.protocol === "file:";

const router = createRouter({
  history: useHashHistory ? createWebHashHistory() : createWebHistory(),
  routes,
});

export default router;
