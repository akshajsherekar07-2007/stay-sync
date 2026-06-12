/**
 * Auth Store — Zustand store for authentication state.
 *
 * Manages: user data, access token, authentication status, initialization.
 * Access token is persisted in localStorage. Refresh token is HttpOnly cookie
 * (no JS access needed — browser sends it automatically).
 */

import { create } from "zustand";

import type { MeResponse } from "@/types/auth";

interface AuthState {
  /** Current authenticated user (null if not logged in) */
  user: MeResponse | null;
  /** JWT access token */
  accessToken: string | null;
  /** Whether the user is currently authenticated */
  isAuthenticated: boolean;
  /** Whether an auth operation is in progress */
  isLoading: boolean;
  /** Whether the initial auth check on app boot has completed */
  isInitialized: boolean;

  // ── Actions ──────────────────────────────────────────────────

  /** Set auth state after login/register */
  setAuth: (user: MeResponse, token: string) => void;
  /** Clear all auth state (logout) */
  clearAuth: () => void;
  /** Partially update user data */
  updateUser: (partial: Partial<MeResponse>) => void;
  /** Update just the access token (after refresh) */
  setToken: (token: string) => void;
  /** Set loading state */
  setLoading: (loading: boolean) => void;
  /** Mark initialization as complete */
  setInitialized: (initialized: boolean) => void;
}

const STORAGE_KEY = "staysync-access-token";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem(STORAGE_KEY),
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,

  setAuth: (user, token) => {
    localStorage.setItem(STORAGE_KEY, token);
    set({
      user,
      accessToken: token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  clearAuth: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  updateUser: (partial) =>
    set((state) => ({
      user: state.user ? { ...state.user, ...partial } : null,
    })),

  setToken: (token) => {
    localStorage.setItem(STORAGE_KEY, token);
    set({ accessToken: token });
  },

  setLoading: (loading) => set({ isLoading: loading }),

  setInitialized: (initialized) => set({ isInitialized: initialized }),
}));
