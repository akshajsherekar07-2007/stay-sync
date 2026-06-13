import { apiClient } from "../lib/axios";
import type { PaginatedResponse, ApiResponse } from "../types/api";
import type { PropertyListItem, PropertyRead, ImageRead, FloorRead, RoomRead, BedRead, AmenityRead } from "../types/property";

export interface ListPropertiesParams {
  city?: string;
  state?: string;
  property_type?: string;
  gender_preference?: string;
  price_min?: number;
  price_max?: number;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const propertyService = {
  /**
   * List properties with optional filters
   */
  async listProperties(params?: ListPropertiesParams): Promise<PaginatedResponse<PropertyListItem>> {
    const response = await apiClient.get<PaginatedResponse<PropertyListItem>>("/properties", {
      params,
    });
    return response.data;
  },

  /**
   * Fetch full details for a single property
   */
  async getProperty(id: string): Promise<ApiResponse<PropertyRead>> {
    const response = await apiClient.get<ApiResponse<PropertyRead>>(`/properties/${id}`);
    return response.data;
  },

  /**
   * Fetch public images for a property
   */
  async getPropertyImages(propertyId: string): Promise<ApiResponse<ImageRead[]>> {
    const response = await apiClient.get<ApiResponse<ImageRead[]>>(`/properties/${propertyId}/images`);
    return response.data;
  },

  /**
   * Fetch public floors for a property
   */
  async getPropertyFloors(propertyId: string): Promise<ApiResponse<FloorRead[]>> {
    const response = await apiClient.get<ApiResponse<FloorRead[]>>(`/properties/${propertyId}/floors`);
    return response.data;
  },

  /**
   * Fetch public rooms for a floor
   */
  async getFloorRooms(floorId: string): Promise<ApiResponse<RoomRead[]>> {
    const response = await apiClient.get<ApiResponse<RoomRead[]>>(`/floors/${floorId}/rooms`);
    return response.data;
  },

  /**
   * Fetch public beds for a room
   */
  async getRoomBeds(roomId: string): Promise<ApiResponse<BedRead[]>> {
    const response = await apiClient.get<ApiResponse<BedRead[]>>(`/rooms/${roomId}/beds`);
    return response.data;
  },

  /**
   * Fetch all amenities from the master catalog
   */
  async listAmenities(): Promise<ApiResponse<AmenityRead[]>> {
    const response = await apiClient.get<ApiResponse<AmenityRead[]>>("/amenities");
    return response.data;
  },
};
