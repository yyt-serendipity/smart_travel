import { createRouter, createWebHistory } from "vue-router";

import AdminView from "../views/AdminView.vue";
import AttractionDetailView from "../views/AttractionDetailView.vue";
import AttractionListView from "../views/AttractionListView.vue";
import CityDetailView from "../views/CityDetailView.vue";
import CityListView from "../views/CityListView.vue";
import CommunityView from "../views/CommunityView.vue";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import PlannerView from "../views/PlannerView.vue";
import PostDetailView from "../views/PostDetailView.vue";
import ProfileView from "../views/ProfileView.vue";
import RegisterView from "../views/RegisterView.vue";
import { authState } from "../stores/auth";


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/cities", name: "cities", component: CityListView },
    { path: "/cities/:id", name: "city-detail", component: CityDetailView, props: true },
    { path: "/attractions", name: "attractions", component: AttractionListView },
    { path: "/attractions/:id", name: "attraction-detail", component: AttractionDetailView, props: true },
    { path: "/planner", name: "planner", component: PlannerView },
    { path: "/community", name: "community", component: CommunityView },
    { path: "/community/:id", name: "post-detail", component: PostDetailView, props: true },
    { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true, transition: "auth-swap" } },
    { path: "/register", name: "register", component: RegisterView, meta: { guestOnly: true, transition: "auth-swap" } },
    { path: "/profile", name: "profile", component: ProfileView, meta: { requiresAuth: true } },
    { path: "/backoffice", name: "backoffice", component: AdminView, meta: { requiresAuth: true, requiresAdmin: true, layout: "admin", transition: "admin-pane" } },
    { path: "/console", redirect: { name: "backoffice" } },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

// Stop protected pages from mounting when the local auth state already tells us the route is invalid.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !authState.token) {
    return { name: "login" };
  }
  if (to.meta.guestOnly && authState.token) {
    return { name: authState.user?.is_staff ? "backoffice" : "home" };
  }
  if (to.meta.requiresAdmin && !authState.user?.is_staff) {
    return { name: "home" };
  }
  return true;
});


export default router;
