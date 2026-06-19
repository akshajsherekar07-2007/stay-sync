import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BedDouble, Lock, Layers, Key, Zap } from "lucide-react";
import { toast } from "sonner";

import { ownerPropertyService } from "../../../services/ownerPropertyService";
import { Button } from "../../../components/ui/Button";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import { EmptyState } from "../../../components/common/EmptyState";
import type { PropertyRead, BedRead } from "../../../types/property";

// Extended types that include hierarchy from PropertyRead
interface FloorWithRooms {
  id: string;
  floor_number: number;
  name: string | null;
  rooms: RoomWithBeds[];
}

interface RoomWithBeds {
  id: string;
  room_number: string;
  name: string | null;
  sharing_type: string;
  price_per_bed: number;
  beds: BedRead[];
}

const STATUS_OPTIONS = [
  { value: "vacant", label: "Vacant", colorClass: "bg-[#00c853] text-white hover:bg-[#00c853]/90" },
  { value: "held", label: "Hold", colorClass: "bg-[#ff9800] text-white hover:bg-[#ff9800]/90" },
  { value: "occupied", label: "Occupied", colorClass: "bg-[#e91e63] text-white hover:bg-[#e91e63]/90" }
] as const;

export default function ManageBedsPage() {
  const { id: propertyId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [updatingBedId, setUpdatingBedId] = useState<string | null>(null);

  // Fetch full property detail to get the floor → room → bed hierarchy
  const { data: property, isLoading: isPropertyLoading } = useQuery({
    queryKey: ["propertyDetailForBeds", propertyId],
    queryFn: async () => {
      const { apiClient } = await import("../../../lib/axios");
      const response = await apiClient.get(`/properties/${propertyId}`);
      return response.data.data as PropertyRead & { floors?: FloorWithRooms[] };
    },
    enabled: !!propertyId,
  });

  const statusMutation = useMutation({
    mutationFn: ({ bedId, status }: { bedId: string; status: string }) =>
      ownerPropertyService.updateBedStatus(bedId, status),
    onSuccess: () => {
      toast.success("Bed status updated successfully.");
      queryClient.invalidateQueries({ queryKey: ["propertyDetailForBeds", propertyId] });
      queryClient.invalidateQueries({ queryKey: ["ownedProperties"] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
      setUpdatingBedId(null);
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || error.response?.data?.detail || "Failed to update bed status.";
      toast.error(message);
      setUpdatingBedId(null);
    },
  });

  const handleStatusChange = (bedId: string, newStatus: string) => {
    setUpdatingBedId(bedId);
    statusMutation.mutate({ bedId, status: newStatus });
  };

  const floors: FloorWithRooms[] = (property as any)?.floors || [];

  if (isPropertyLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[50vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8 w-full max-w-[1400px] mx-auto pb-12 animate-fade-in">
      {/* Header section similar to image 1 */}
      <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" asChild className="shrink-0 mt-1">
            <Link to="/owner/properties">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold uppercase tracking-wider">
                <Zap className="h-3 w-3" />
                Direct State Override
              </span>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-text">
              Live Beds Status Control
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Instantly switch bed status to vacant, holding, or occupied without waiting for request reviews.
            </p>
          </div>
        </div>
      </div>

      {/* Beds by Floor → Room */}
      {floors.length === 0 ? (
        <EmptyState
          icon={<BedDouble className="h-10 w-10 text-text-tertiary" />}
          title="No Beds Configured"
          description="This property has no floors, rooms, or beds configured yet."
        />
      ) : (
        <div className="space-y-8">
          {floors.map((floor) => (
            <div key={floor.id} className="bg-white rounded-3xl border border-border/60 shadow-sm overflow-hidden p-6">
              {/* Floor Header */}
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-border/40">
                <div className="flex items-center gap-3">
                  <Layers className="h-6 w-6 text-amber-700 shrink-0" />
                  <h2 className="text-xl font-bold text-text">
                    {floor.floor_number}{floor.floor_number === 1 ? 'st' : floor.floor_number === 2 ? 'nd' : floor.floor_number === 3 ? 'rd' : 'th'} Floor
                    {floor.name && <span className="font-normal text-text-secondary ml-2">— {floor.name}</span>}
                  </h2>
                </div>
                <div className="text-sm font-medium text-text-tertiary">
                  ({floor.rooms.length} Rooms)
                </div>
              </div>

              {floor.rooms.length === 0 ? (
                <div className="py-8 text-sm text-text-tertiary text-center">
                  No rooms on this floor.
                </div>
              ) : (
                <div className="grid gap-6 md:grid-cols-2">
                  {floor.rooms.map((room) => (
                    <div key={room.id} className="border border-border/50 rounded-2xl p-5 bg-white shadow-sm hover:shadow-md transition-shadow">
                      {/* Room Header */}
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2">
                          <Key className="h-5 w-5 text-amber-500 shrink-0" />
                          <h3 className="text-lg font-bold text-text">
                            Room {room.room_number} {room.sharing_type && <span className="font-medium text-text-secondary capitalize">({room.sharing_type} Share)</span>}
                          </h3>
                        </div>
                        {/* Assuming property level amenities for now, or just placeholder as in image */}
                        <div className="text-xs text-text-tertiary bg-bg-secondary px-2.5 py-1 rounded-md font-medium">
                          Amenities: Basic
                        </div>
                      </div>

                      {/* Beds List */}
                      {room.beds.length === 0 ? (
                        <div className="py-4 text-sm text-text-tertiary text-center">No beds in this room.</div>
                      ) : (
                        <div className="space-y-4">
                          {room.beds.map((bed) => {
                            const hasActiveHold = !!bed.current_hold_id;
                            const isUpdating = updatingBedId === bed.id;
                            const isLocked = hasActiveHold && bed.status === "held";
                            
                            // Parse sharing type to a number if possible
                            const shareMap: Record<string, number> = { single: 1, double: 2, triple: 3, quad: 4 };
                            const numShares = shareMap[room.sharing_type.toLowerCase()] || 1;

                            return (
                              <div key={bed.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-1">
                                {/* Bed Info (Left side) */}
                                <div className="flex items-start gap-3">
                                  <BedDouble className="h-5 w-5 text-text-tertiary shrink-0 mt-0.5" />
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-text text-sm">
                                        Bed {bed.bed_number}
                                        {bed.label && ` - ${bed.label}`}
                                      </span>
                                      <span className="text-xs text-text-tertiary font-medium">({numShares} Share)</span>
                                    </div>
                                    <div className="flex items-center gap-3 mt-1">
                                      <span className="text-xs font-semibold text-text-secondary">
                                        ₹{bed.price || room.price_per_bed}/mo
                                      </span>
                                      
                                      {/* Hold notification badge if locked */}
                                      {isLocked && (
                                        <span className="flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                                          <Lock className="h-2.5 w-2.5" />
                                          Active Hold
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* Status Selector Pill (Right side) */}
                                <div className="flex bg-slate-100 rounded-lg p-1 border border-slate-200 shrink-0">
                                  {STATUS_OPTIONS.map((option) => {
                                    const isSelected = bed.status === option.value;
                                    return (
                                      <button
                                        key={option.value}
                                        disabled={isLocked || isUpdating || isSelected}
                                        onClick={() => handleStatusChange(bed.id, option.value)}
                                        className={`
                                          text-[13px] font-bold px-4 py-1.5 rounded-md transition-all duration-200
                                          ${isSelected 
                                            ? `${option.colorClass} shadow-sm` 
                                            : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
                                          }
                                          ${isLocked ? "opacity-50 cursor-not-allowed" : ""}
                                          ${isUpdating && !isSelected ? "opacity-50 cursor-wait" : ""}
                                        `}
                                      >
                                        {isUpdating && option.value !== bed.status && updatingBedId === bed.id ? "..." : option.label}
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
