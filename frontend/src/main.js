import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import { fetchMe } from "./services/api";
import { authState } from "./stores/auth";
import "./styles.css";


async function bootstrap() {
  if (authState.token && !authState.user) {
    try {
      await fetchMe();
    } catch {
      // Invalid token is cleared by the API interceptor.
    }
  }
  createApp(App).use(router).mount("#app");
}

bootstrap();
