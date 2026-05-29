import axios from "axios";
import type { AxiosInstance } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/**
 * Pre-configured Axios instance for API calls.
 * Token interceptors will be added in Phase 1.4 (auth system).
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor (Phase 1.4: attach JWT) ─────────────
// apiClient.interceptors.request.use(...)

// ── Response Interceptor (Phase 1.4: token refresh) ─────────
// apiClient.interceptors.response.use(...)
