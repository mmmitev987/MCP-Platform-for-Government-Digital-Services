import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true, // send cookies with every request (needed for csrf_token cookie)
});

// ── CSRF token setup ──────────────────────────────────────────────────────────
// Fetch a CSRF token from the backend on app load and store it in memory.
// The token is also set as a cookie by the backend (Double Submit Cookie pattern).
let csrfToken = null;

export async function initCsrf() {
  try {
    const { data } = await client.get("/api/auth/csrf-token");
    csrfToken = data.csrf_token;
  } catch {
    // If the backend is unreachable on init, requests will fail with 403
    // and the user will be prompted to reload.
  }
}

// ── Request interceptor: attach JWT + CSRF token ──────────────────────────────
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;

  // Attach CSRF token header on every state-changing request
  const mutating = ["post", "put", "patch", "delete"];
  if (csrfToken && mutating.includes(config.method?.toLowerCase())) {
    config.headers["X-CSRF-Token"] = csrfToken;
  }

  return config;
});

// ── Response interceptor: handle 401 + auto-refresh CSRF on 403 ──────────────
client.interceptors.response.use(
  (res) => res,
  async (err) => {
    // If a 403 comes back and we haven't already retried, the CSRF token was
    // likely missing or stale (e.g. backend restarted while frontend was open).
    // Re-fetch the token and replay the original request exactly once.
    if (err.response?.status === 403 && !err.config._csrfRetry) {
      err.config._csrfRetry = true;
      await initCsrf();
      const mutating = ["post", "put", "patch", "delete"];
      if (csrfToken && mutating.includes(err.config.method?.toLowerCase())) {
        err.config.headers["X-CSRF-Token"] = csrfToken;
      }
      return client(err.config);
    }

    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/signin";
    }
    return Promise.reject(err);
  }
);

export default client;
