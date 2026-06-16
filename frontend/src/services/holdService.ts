import { apiClient } from "../lib/axios";
import type { PaginatedResponse, ApiResponse } from "../types/api";
import type { HoldRequestCreate, HoldRequestUpdate, HoldRequestRead } from "../types/hold";
import { HoldStatus } from "../types/hold";

export interface ListHoldsParams {
  status?: HoldStatus;
  page?: number;
  page_size?: number;
}

export const holdService = {
  /**
   * Request a new hold
   */
  async requestHold(data: HoldRequestCreate): Promise<ApiResponse<HoldRequestRead>> {
    const response = await apiClient.post<ApiResponse<HoldRequestRead>>("/holds", data);
    return response.data;
  },

  /**
   * List my holds (Student)
   */
  async listMyHolds(params?: ListHoldsParams): Promise<PaginatedResponse<HoldRequestRead>> {
    const response = await apiClient.get<PaginatedResponse<HoldRequestRead>>("/holds/me", { params });
    return response.data;
  },

  /**
   * List holds for a specific property (Owner)
   */
  async listPropertyHolds(propertyId: string, params?: ListHoldsParams): Promise<PaginatedResponse<HoldRequestRead>> {
    const response = await apiClient.get<PaginatedResponse<HoldRequestRead>>(`/holds/property/${propertyId}`, { params });
    return response.data;
  },

  /**
   * Get details of a specific hold
   */
  async getHold(holdId: string): Promise<ApiResponse<HoldRequestRead>> {
    const response = await apiClient.get<ApiResponse<HoldRequestRead>>(`/holds/${holdId}`);
    return response.data;
  },

  /**
   * Approve a pending hold (Owner)
   */
  async approveHold(holdId: string): Promise<ApiResponse<HoldRequestRead>> {
    const response = await apiClient.post<ApiResponse<HoldRequestRead>>(`/holds/${holdId}/approve`);
    return response.data;
  },

  /**
   * Reject a pending hold (Owner)
   */
  async rejectHold(holdId: string, data: HoldRequestUpdate): Promise<ApiResponse<HoldRequestRead>> {
    const response = await apiClient.post<ApiResponse<HoldRequestRead>>(`/holds/${holdId}/reject`, data);
    return response.data;
  },

  /**
   * Cancel my hold (Student)
   */
  async cancelHold(holdId: string): Promise<ApiResponse<HoldRequestRead>> {
    const response = await apiClient.post<ApiResponse<HoldRequestRead>>(`/holds/${holdId}/cancel`);
    return response.data;
  },
};
