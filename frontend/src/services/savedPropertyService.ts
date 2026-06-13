import { apiClient } from "../lib/axios";
import type { MessageResponse, PaginatedResponse } from "../types/api";
import type { PropertyListItem } from "../types/property";

export const savedPropertyService = {
  /**
   * Save a property to the student's wishlist
   */
  async saveProperty(propertyId: string): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>(`/properties/${propertyId}/save`);
    return response.data;
  },

  /**
   * Remove a property from the student's wishlist
   */
  async unsaveProperty(propertyId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/properties/${propertyId}/save`);
    return response.data;
  },

  /**
   * Fetch saved properties for the current student.
   * Performs client-side filtering on the property list.
   */
  async listSavedProperties(): Promise<PaginatedResponse<PropertyListItem>> {
    const response = await apiClient.get<PaginatedResponse<PropertyListItem>>("/properties");
    // Filter where is_saved is true
    const saved = response.data.data.filter((item) => item.is_saved);
    return {
      ...response.data,
      data: saved,
      pagination: {
        ...response.data.pagination,
        total_items: saved.length,
        total_pages: Math.ceil(saved.length / response.data.pagination.page_size),
      },
    };
  },
};
