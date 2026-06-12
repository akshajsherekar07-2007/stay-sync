import { useState } from "react";
import { useAuthStore } from "../../../stores/authStore";
import { authService } from "../../../services/authService";
import { userService } from "../../../services/userService";
import type { LoginRequest, RegisterRequest } from "./types";

export function useAuth() {
  const { user, isAuthenticated, isLoading, setAuth, clearAuth, setToken, setLoading } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const login = async (data: LoginRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.login(data);
      // Set access token in local storage and store
      setToken(response.data.token.access_token);
      // Fetch full profile info
      const meResponse = await userService.getMe();
      setAuth(meResponse.data, response.data.token.access_token);
    } catch (err: any) {
      const errMsg = err.response?.data?.error?.message || "Login failed. Please check your credentials.";
      setError(errMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.register(data);
      // Set access token
      setToken(response.data.token.access_token);
      // Fetch full profile info
      const meResponse = await userService.getMe();
      setAuth(meResponse.data, response.data.token.access_token);
    } catch (err: any) {
      const errMsg = err.response?.data?.error?.message || "Registration failed. Please try again.";
      setError(errMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
    } catch (err) {
      console.error("Logout error (proceeding with local cleanup):", err);
    } finally {
      clearAuth();
      setLoading(false);
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
  };
}
