import { savedPropertyService } from "./savedPropertyService";
import { ownerPropertyService } from "./ownerPropertyService";
import type { PropertyListItem } from "../types/property";

export interface StudentDashboardData {
  active_holds_count: number;
  saved_properties: PropertyListItem[];
}

export interface OwnerDashboardData {
  listings_count: number;
  total_beds: number;
  occupied_beds: number;
  occupied_bed_percentage: number;
  revenue_projection: number;
}

export const dashboardService = {
  /**
   * Aggregate student dashboard details.
   * Returns saved wishlist items and stubs active holds count (holds system is implemented in Phase 2).
   */
  async getStudentDashboardData(): Promise<StudentDashboardData> {
    const savedRes = await savedPropertyService.listSavedProperties();
    return {
      active_holds_count: 0, // Placeholder for Phase 2 Holds integration
      saved_properties: savedRes.data,
    };
  },

  /**
   * Aggregate owner dashboard metrics from their properties catalog.
   * Calculates listings, bed occupancy percentages, and estimated monthly revenues.
   */
  async getOwnerDashboardData(): Promise<OwnerDashboardData> {
    const propertiesRes = await ownerPropertyService.listOwnedProperties();
    const properties = propertiesRes.data;

    let totalBeds = 0;
    let availableBeds = 0;
    let revenueProjection = 0;

    properties.forEach((prop) => {
      totalBeds += prop.total_beds;
      availableBeds += prop.available_beds;
      
      // Revenue calculation uses min_price multiplied by occupied beds
      const occupied = prop.total_beds - prop.available_beds;
      revenueProjection += occupied * (prop.min_price || 0);
    });

    const occupiedBeds = totalBeds - availableBeds;
    const occupiedBedPercentage = totalBeds > 0 ? Math.round((occupiedBeds / totalBeds) * 100) : 0;

    return {
      listings_count: properties.length,
      total_beds: totalBeds,
      occupied_beds: occupiedBeds,
      occupied_bed_percentage: occupiedBedPercentage,
      revenue_projection: revenueProjection,
    };
  },
};
