import { apiClient } from "../lib/axios";
import type { ApiResponse, PaginatedResponse } from "../types/api";
import type { WaitlistEntryCreate, WaitlistEntryRead, WaitlistPositionResponse } from "../types/waitlist";

export interface ListWaitlistsParams {
  status?: string;
  page?: number;
  page_size?: number;
}

export const waitlistService = {
  /**
   * Join a bed's waitlist
   */
  async joinWaitlist(data: WaitlistEntryCreate): Promise<ApiResponse<WaitlistEntryRead>> {
    const response = await apiClient.post<ApiResponse<WaitlistEntryRead>>("/waitlists", data);
    return response.data;
  },

  /**
   * Get paginated waitlist entries for the authenticated student
   */
  async getMyWaitlists(params?: ListWaitlistsParams): Promise<PaginatedResponse<WaitlistEntryRead>> {
    const response = await apiClient.get<PaginatedResponse<WaitlistEntryRead>>("/waitlists/me", {
      params,
    });
    return response.data;
  },

  /**
   * View active queue for a bed (Owner only)
   */
  async getBedQueue(bedId: string): Promise<ApiResponse<WaitlistEntryRead[]>> {
    const response = await apiClient.get<ApiResponse<WaitlistEntryRead[]>>(`/waitlists/bed/${bedId}`);
    return response.data;
  },

  /**
   * Get student's queue position for a bed
   */
  async getQueuePosition(bedId: string): Promise<ApiResponse<WaitlistPositionResponse>> {
    const response = await apiClient.get<ApiResponse<WaitlistPositionResponse>>(`/waitlists/bed/${bedId}/position`);
    return response.data;
  },

  /**
   * Cancel my waitlist entry
   */
  async cancelWaitlist(entryId: string): Promise<ApiResponse<WaitlistEntryRead>> {
    const response = await apiClient.post<ApiResponse<WaitlistEntryRead>>(`/waitlists/${entryId}/cancel`);
    return response.data;
  },
};
