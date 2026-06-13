import { useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle } from "lucide-react";

import { propertyService } from "../../../services/propertyService";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import { Button } from "../../../components/ui/Button";
import { Link } from "react-router-dom";
import PropertyForm from "../components/PropertyForm";

export default function EditPropertyPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const stepParam = searchParams.get("step");
  const initialStep = stepParam ? parseInt(stepParam, 10) : 1;

  // Unified Query to load the full property details and hierarchy
  const { data: fullPropertyData, isLoading, isError } = useQuery({
    queryKey: ["fullProperty", id],
    queryFn: async () => {
      // 1. Base property details
      const propRes = await propertyService.getProperty(id!);
      const property = propRes.data;

      // 2. Images
      const imagesRes = await propertyService.getPropertyImages(id!);
      const images = imagesRes.data;

      // 3. Floors hierarchy
      const floorsRes = await propertyService.getPropertyFloors(id!);
      const floors = floorsRes.data;

      // 4. Resolve nested rooms & beds
      const fullFloors = await Promise.all(
        floors.map(async (floor) => {
          const roomsRes = await propertyService.getFloorRooms(floor.id);
          const rooms = roomsRes.data;

          const fullRooms = await Promise.all(
            rooms.map(async (room) => {
              const bedsRes = await propertyService.getRoomBeds(room.id);
              const beds = bedsRes.data;

              return {
                id: room.id,
                room_number: room.room_number,
                name: room.name || "",
                sharing_type: room.sharing_type,
                price_per_bed: Number(room.price_per_bed),
                description: room.description || "",
                has_attached_bath: room.has_attached_bath,
                has_ac: room.has_ac,
                has_balcony: room.has_balcony,
                sort_order: room.sort_order,
                beds: beds.map((bed) => ({
                  id: bed.id,
                  bed_number: bed.bed_number,
                  label: bed.label || "",
                  price: bed.price ? Number(bed.price) : null,
                  sort_order: bed.sort_order,
                })),
              };
            })
          );

          return {
            id: floor.id,
            floor_number: floor.floor_number,
            name: floor.name || "",
            description: floor.description || "",
            sort_order: floor.sort_order,
            rooms: fullRooms,
          };
        })
      );

      return {
        property,
        images,
        floors: fullFloors,
      };
    },
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !fullPropertyData) {
    return (
      <div className="mx-auto max-w-md py-20 text-center px-4">
        <AlertTriangle className="mx-auto h-12 w-12 text-danger mb-4" />
        <h2 className="text-2xl font-bold text-text">Failed to load property</h2>
        <p className="mt-2 text-text-secondary">
          The property details could not be retrieved from the server.
        </p>
        <div className="mt-6">
          <Button asChild>
            <Link to="/owner/properties">Back to My Properties</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Edit Accommodation</h1>
        <p className="text-text-secondary text-sm mt-1">
          Modify the configuration, details, and inventory structure for <span className="font-semibold text-text">{fullPropertyData.property.name}</span>.
        </p>
      </div>

      <PropertyForm 
        propertyId={id} 
        initialData={fullPropertyData} 
        initialStep={initialStep} 
      />
    </div>
  );
}
