import { createRouter, createWebHistory } from "vue-router";
import LandingPage from "./views/LandingPage.vue";
import PayrollTool from "./views/PayrollTool.vue";

const routes = [
  { path: "/", name: "landing", component: LandingPage },
  { path: "/payroll", name: "payroll", component: PayrollTool },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
