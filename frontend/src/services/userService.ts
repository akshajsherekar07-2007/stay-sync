import { apiClient } from "@/lib/axios";
import type { ApiResponse } from "@/types/api";
import type { MeResponse, ProfileRead, ProfileUpdate } from "@/types/auth";

export const userService = {
  async getMe(): Promise<ApiResponse<MeResponse>> {
    const response = await apiClient.get<ApiResponse<MeResponse>>("/users/me");
    return response.data;
  },

  async updateProfile(data: ProfileUpdate): Promise<ApiResponse<ProfileRead>> {
    const response = await apiClient.patch<ApiResponse<ProfileRead>>("/users/me/profile", data);
    return response.data;
  }
};
