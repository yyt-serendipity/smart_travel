import { reactive } from "vue";


const storedUser = localStorage.getItem("smart_journey_user");

export const authState = reactive({
  token: localStorage.getItem("smart_journey_token") || "",
  user: storedUser ? JSON.parse(storedUser) : null,
});


export function setAuth(token, user) {
  authState.token = token;
  authState.user = user;
  localStorage.setItem("smart_journey_token", token);
  localStorage.setItem("smart_journey_user", JSON.stringify(user));
}


export function clearAuth() {
  authState.token = "";
  authState.user = null;
  localStorage.removeItem("smart_journey_token");
  localStorage.removeItem("smart_journey_user");
}
