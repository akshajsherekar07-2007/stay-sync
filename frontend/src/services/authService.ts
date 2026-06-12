import { apiClient } from "../lib/axios";
import type { ApiResponse, MessageResponse } from "../types/api";
import type { LoginRequest, RegisterRequest, LoginResponse } from "../types/auth";

export const authService = {
  async register(data: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>("/auth/register", data);
    return response.data;
  },

  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>("/auth/login", data);
    return response.data;
  },

  async refresh(): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post<ApiResponse<LoginResponse>>("/auth/refresh");
    return response.data;
  },

  async logout(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>("/auth/logout");
    return response.data;
  },

  async logoutAll(): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>("/auth/logout-all");
    return response.data;
  },

  async verifyEmail(token: string): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>(`/auth/verify-email?token=${encodeURIComponent(token)}`);
    return response.data;
  }
};
