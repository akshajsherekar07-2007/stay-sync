import { apiClient } from "../lib/axios";
import type { PaginatedResponse, ApiResponse } from "../types/api";
import type { NotificationRead } from "../types/notification";

export interface ListNotificationsParams {
  unread_only?: boolean;
  page?: number;
  page_size?: number;
}

export const notificationService = {
  /**
   * List user notifications
   */
  async listNotifications(params?: ListNotificationsParams): Promise<PaginatedResponse<NotificationRead>> {
    const response = await apiClient.get<PaginatedResponse<NotificationRead>>("/notifications", { params });
    return response.data;
  },

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<number> {
    const response = await apiClient.get<ApiResponse<{ unread_count: number }>>("/notifications/unread-count");
    return response.data.data.unread_count;
  },

  /**
   * Mark a single notification as read
   */
  async markAsRead(id: string): Promise<ApiResponse<NotificationRead>> {
    const response = await apiClient.post<ApiResponse<NotificationRead>>(`/notifications/${id}/read`);
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<ApiResponse<{ message: string }>> {
    const response = await apiClient.post<ApiResponse<{ message: string }>>("/notifications/read-all");
    return response.data;
  },
};
