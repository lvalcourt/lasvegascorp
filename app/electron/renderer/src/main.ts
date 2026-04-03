import { createApp } from "vue";
import App from "./App.vue";
import "./styles.css";
import router from "./router";
import { hydrateSession } from "./auth";

async function bootstrap() {
  await hydrateSession();
  createApp(App).use(router).mount("#app");
}

void bootstrap();
