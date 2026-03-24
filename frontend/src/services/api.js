import axios from "axios";

import { authState, clearAuth, setAuth } from "../stores/auth";


const client = axios.create({
  baseURL: "/api",
  timeout: 12000,
});

client.interceptors.request.use((config) => {
  if (authState.token) {
    config.headers.Authorization = `Token ${authState.token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && authState.token) {
      clearAuth();
    }
    return Promise.reject(error);
  },
);


function unwrap(response) {
  return response.data;
}


// Register a new user and store the returned token locally.
export async function register(payload) {
  const data = unwrap(await client.post("/auth/register/", payload));
  setAuth(data.token, data.user);
  return data;
}

// Login and cache the authenticated user info.
export async function login(payload) {
  const data = unwrap(await client.post("/auth/login/", payload));
  setAuth(data.token, data.user);
  return data;
}

// Logout the current user and clear local auth state.
export async function logout() {
  if (authState.token) {
    await client.post("/auth/logout/");
  }
  clearAuth();
}

// Restore the current user from an existing token.
export async function fetchMe() {
  const data = unwrap(await client.get("/auth/me/"));
  setAuth(authState.token, data.user);
  return data.user;
}

// Read the personal profile page data.
export async function getProfile() {
  return unwrap(await client.get("/profile/me/"));
}

// Update the personal profile page data.
export async function updateProfile(payload) {
  const data = unwrap(await client.patch("/profile/me/", payload));
  if (authState.user) {
    setAuth(authState.token, data.user);
  }
  return data;
}

// Upload a media file and return the saved URL.
export async function uploadMedia(file, category = "attachment") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  return unwrap(
    await client.post("/uploads/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),
  );
}

// Load the home page overview payload.
export async function getOverview() {
  return unwrap(await client.get("/overview/"));
}

// Load the home page province map overview payload.
export async function getProvinceMapOverview() {
  return unwrap(await client.get("/maps/provinces/overview/"));
}

// Load a single province map payload with city markers.
export async function getProvinceMapDetail(province) {
  return unwrap(await client.get("/maps/provinces/detail/", { params: { province } }));
}

// Load the travel city list with optional filters.
export async function getCities(params = {}) {
  return unwrap(await client.get("/cities/", { params }));
}

// Load a single city detail page.
export async function getCity(id) {
  return unwrap(await client.get(`/cities/${id}/`));
}

// Load weather data for a single city detail page.
export async function getCityWeather(id) {
  return unwrap(await client.get(`/cities/${id}/weather/`));
}

// Load a single attraction detail page.
export async function getAttraction(id) {
  return unwrap(await client.get(`/attractions/${id}/`));
}

// Request recommended cities for the planner.
export async function recommendCities(params = {}) {
  return unwrap(await client.get("/cities/recommend/", { params }));
}

// Load the attraction list with optional filters.
export async function getAttractions(params = {}) {
  return unwrap(await client.get("/attractions/", { params }));
}

// Load the community post feed.
export async function getPosts(params = {}) {
  return unwrap(await client.get("/posts/", { params }));
}

// Load one community post detail.
export async function getPost(id) {
  return unwrap(await client.get(`/posts/${id}/`));
}

// Create a new community post.
export async function createPost(payload) {
  return unwrap(await client.post("/posts/", payload));
}

// Toggle like status for a post.
export async function toggleLike(postId) {
  return unwrap(await client.post(`/posts/${postId}/like/`));
}

// Toggle favorite status for a post.
export async function toggleFavorite(postId) {
  return unwrap(await client.post(`/posts/${postId}/favorite/`));
}

// Load favorited posts for the current user.
export async function getFavoritePosts() {
  return unwrap(await client.get("/posts/favorites/"));
}

// Add a comment to a post.
export async function addComment(postId, payload) {
  return unwrap(await client.post(`/posts/${postId}/comment/`, payload));
}

// Generate an AI travel plan result.
export async function generatePlan(payload) {
  return unwrap(
    await client.post("/planner/generate/", payload, {
      timeout: 40000,
    }),
  );
}

// Load saved plans for the current user.
export async function getPlans() {
  return unwrap(await client.get("/plans/"));
}

// Load the backoffice dashboard summary.
export async function getAdminSummary() {
  return unwrap(await client.get("/backoffice/summary/"));
}

// Load the backoffice user list.
export async function getAdminUsers(params = {}) {
  return unwrap(await client.get("/backoffice/users/", { params }));
}

// Update a user in the backoffice.
export async function saveAdminUser(payload) {
  return unwrap(await client.put(`/backoffice/users/${payload.id}/`, payload));
}

// Delete a user in the backoffice.
export async function deleteAdminUser(id) {
  return unwrap(await client.delete(`/backoffice/users/${id}/`));
}

// Load the backoffice operation log list.
export async function getAdminLogs(params = {}) {
  return unwrap(await client.get("/backoffice/logs/", { params }));
}

// Load the backoffice city list.
export async function getAdminCities(params = {}) {
  return unwrap(await client.get("/backoffice/cities/", { params }));
}

// Create or update a city in the backoffice.
export async function saveAdminCity(payload) {
  if (payload.id) {
    return unwrap(await client.put(`/backoffice/cities/${payload.id}/`, payload));
  }
  return unwrap(await client.post("/backoffice/cities/", payload));
}

// Delete a city in the backoffice.
export async function deleteAdminCity(id) {
  return unwrap(await client.delete(`/backoffice/cities/${id}/`));
}

// Load the backoffice attraction list.
export async function getAdminAttractions(params = {}) {
  return unwrap(await client.get("/backoffice/attractions/", { params }));
}

// Create or update an attraction in the backoffice.
export async function saveAdminAttraction(payload) {
  if (payload.id) {
    return unwrap(await client.put(`/backoffice/attractions/${payload.id}/`, payload));
  }
  return unwrap(await client.post("/backoffice/attractions/", payload));
}

// Delete an attraction in the backoffice.
export async function deleteAdminAttraction(id) {
  return unwrap(await client.delete(`/backoffice/attractions/${id}/`));
}

// Load the backoffice post list.
export async function getAdminPosts(params = {}) {
  return unwrap(await client.get("/backoffice/posts/", { params }));
}

// Delete a post in the backoffice.
export async function deleteAdminPost(id) {
  return unwrap(await client.delete(`/backoffice/posts/${id}/`));
}

// Import local Excel workbooks into the database.
export async function importExcelDirectory(payload = {}) {
  return unwrap(await client.post("/backoffice/import-excels/", payload));
}

// Upload Excel workbooks from the browser and import them into the database.
export async function importExcelFiles(files, overwrite = false) {
  const formData = new FormData();
  [...files].forEach((file) => {
    formData.append("files", file);
  });
  formData.append("overwrite", overwrite ? "true" : "false");
  return unwrap(
    await client.post("/backoffice/import-excels/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),
  );
}
