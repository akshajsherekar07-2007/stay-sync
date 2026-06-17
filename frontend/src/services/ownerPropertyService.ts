import { apiClient } from "../lib/axios";
import { useAuthStore } from "../stores/authStore";
import type { PaginatedResponse, ApiResponse, MessageResponse } from "../types/api";
import type {
  PropertyListItem,
  PropertyRead,
  PropertyCreate,
  PropertyUpdate,
  ImageRead,
  ImageUpdate,
  ImageReorder,
  AmenityAttach,
  FloorRead,
  RoomRead,
  BedRead,
} from "../types/property";

export const ownerPropertyService = {
  /**
   * Fetch properties owned by the current landlord.
   * Fetches from properties list and filters by owner_id client-side.
   */
  async listOwnedProperties(): Promise<PaginatedResponse<PropertyListItem>> {
    const response = await apiClient.get<PaginatedResponse<PropertyListItem>>("/properties");
    const ownerId = useAuthStore.getState().user?.id;
    const owned = response.data.data.filter((item) => item.owner_id === ownerId);
    return {
      ...response.data,
      data: owned,
      pagination: {
        ...response.data.pagination,
        total_items: owned.length,
        total_pages: Math.ceil(owned.length / response.data.pagination.page_size),
      },
    };
  },

  /**
   * Create a new property listing
   */
  async createProperty(data: PropertyCreate): Promise<ApiResponse<PropertyRead>> {
    const response = await apiClient.post<ApiResponse<PropertyRead>>("/properties", data);
    return response.data;
  },

  /**
   * Partially update a property listing
   */
  async updateProperty(id: string, data: PropertyUpdate): Promise<ApiResponse<PropertyRead>> {
    const response = await apiClient.patch<ApiResponse<PropertyRead>>(`/properties/${id}`, data);
    return response.data;
  },

  /**
   * Soft-delete a property listing
   */
  async deleteProperty(id: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/properties/${id}`);
    return response.data;
  },

  /**
   * Update the status of a property (e.g. draft -> active)
   */
  async updatePropertyStatus(id: string, status: string): Promise<ApiResponse<PropertyRead>> {
    const response = await apiClient.post<ApiResponse<PropertyRead>>(`/properties/${id}/status`, {
      status,
    });
    return response.data;
  },

  /**
   * Upload an image for a property
   */
  async uploadPropertyImage(
    propertyId: string,
    file: File,
    entityType: string = "property",
    entityId?: string
  ): Promise<ApiResponse<ImageRead>> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<ApiResponse<ImageRead>>(
      `/properties/${propertyId}/images`,
      formData,
      {
        params: {
          entity_type: entityType,
          entity_id: entityId || propertyId,
        },
      }
    );
    return response.data;
  },

  /**
   * Delete an image from a property listing
   */
  async deletePropertyImage(propertyId: string, imageId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/properties/${propertyId}/images/${imageId}`);
    return response.data;
  },

  /**
   * Update metadata on a property image
   */
  async updatePropertyImage(
    propertyId: string,
    imageId: string,
    data: ImageUpdate
  ): Promise<ApiResponse<ImageRead>> {
    const response = await apiClient.patch<ApiResponse<ImageRead>>(
      `/properties/${propertyId}/images/${imageId}`,
      data
    );
    return response.data;
  },

  /**
   * Reorder multiple property images
   */
  async reorderPropertyImages(propertyId: string, data: ImageReorder): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>(`/properties/${propertyId}/images/reorder`, data);
    return response.data;
  },

  /**
   * Attach amenities to a property listing
   */
  async attachAmenities(propertyId: string, data: AmenityAttach): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>(`/properties/${propertyId}/amenities`, data);
    return response.data;
  },

  /**
   * Detach an amenity from a property listing
   */
  async detachAmenity(propertyId: string, amenityId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/properties/${propertyId}/amenities/${amenityId}`);
    return response.data;
  },

  /**
   * Create a new floor
   */
  async createFloor(propertyId: string, data: { floor_number: number; name?: string | null; description?: string | null; sort_order?: number }): Promise<ApiResponse<FloorRead>> {
    const response = await apiClient.post<ApiResponse<FloorRead>>(`/properties/${propertyId}/floors`, data);
    return response.data;
  },

  /**
   * Update a floor
   */
  async updateFloor(floorId: string, data: { floor_number?: number; name?: string | null; description?: string | null; sort_order?: number }): Promise<ApiResponse<FloorRead>> {
    const response = await apiClient.patch<ApiResponse<FloorRead>>(`/floors/${floorId}`, data);
    return response.data;
  },

  /**
   * Delete a floor
   */
  async deleteFloor(floorId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/floors/${floorId}`);
    return response.data;
  },

  /**
   * Create a new room
   */
  async createRoom(floorId: string, data: { room_number: string; name?: string | null; sharing_type: string; price_per_bed: number; description?: string | null; has_attached_bath?: boolean; has_ac?: boolean; has_balcony?: boolean; sort_order?: number }): Promise<ApiResponse<RoomRead>> {
    const response = await apiClient.post<ApiResponse<RoomRead>>(`/floors/${floorId}/rooms`, data);
    return response.data;
  },

  /**
   * Update a room
   */
  async updateRoom(roomId: string, data: { room_number?: string; name?: string | null; sharing_type?: string; price_per_bed?: number; description?: string | null; has_attached_bath?: boolean; has_ac?: boolean; has_balcony?: boolean; sort_order?: number }): Promise<ApiResponse<RoomRead>> {
    const response = await apiClient.patch<ApiResponse<RoomRead>>(`/rooms/${roomId}`, data);
    return response.data;
  },

  /**
   * Delete a room
   */
  async deleteRoom(roomId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/rooms/${roomId}`);
    return response.data;
  },

  /**
   * Create a new bed
   */
  async createBed(roomId: string, data: { bed_number: string; label?: string | null; price?: number | null; sort_order?: number }): Promise<ApiResponse<BedRead>> {
    const response = await apiClient.post<ApiResponse<BedRead>>(`/rooms/${roomId}/beds`, data);
    return response.data;
  },

  /**
   * Update a bed
   */
  async updateBed(bedId: string, data: { bed_number?: string; label?: string | null; price?: number | null; sort_order?: number }): Promise<ApiResponse<BedRead>> {
    const response = await apiClient.patch<ApiResponse<BedRead>>(`/beds/${bedId}`, data);
    return response.data;
  },

  /**
   * Delete a bed
   */
  async deleteBed(bedId: string): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/beds/${bedId}`);
    return response.data;
  },
};

