import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Heart,
  MapPin,
  Building,
  Phone,
  Mail,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Layers,
  Wifi,
  Tv,
  Coffee,
  Shield,
  Clock,
  BedDouble,
  Image as ImageIcon
} from "lucide-react";

import { useAuthStore } from "../../../stores/authStore";
import { propertyService } from "../../../services/propertyService";
import { savedPropertyService } from "../../../services/savedPropertyService";
import { holdService } from "../../../services/holdService";
import { HoldStatus } from "../../../types/enums";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { Separator } from "../../../components/ui/Separator";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import { PropertyDetailsSkeleton } from "../../../components/common/PropertyDetailsSkeleton";
import { RoomCard } from "../components/RoomCard";
import { BedCard } from "../components/BedCard";

export default function PropertyDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuthStore();

  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [selectedFloorId, setSelectedFloorId] = useState<string | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // 1. Fetch Property details
  const { data: propertyResponse, isLoading: isPropertyLoading, isError } = useQuery({
    queryKey: ["property", id],
    queryFn: () => propertyService.getProperty(id!),
    enabled: !!id,
  });

  const property = propertyResponse?.data;

  // 2. Fetch Property images
  const { data: imagesResponse } = useQuery({
    queryKey: ["propertyImages", id],
    queryFn: () => propertyService.getPropertyImages(id!),
    enabled: !!id,
  });

  const images = imagesResponse?.data || [];

  // 3. Fetch Property floors
  const { data: floorsResponse } = useQuery({
    queryKey: ["propertyFloors", id],
    queryFn: () => propertyService.getPropertyFloors(id!),
    enabled: !!id,
  });

  const floors = floorsResponse?.data || [];

  // Auto-select first floor when floors load
  useEffect(() => {
    if (floors.length > 0 && !selectedFloorId) {
      setSelectedFloorId(floors[0].id);
    }
  }, [floors, selectedFloorId]);

  // 4. Fetch Rooms for selected floor
  const { data: roomsResponse, isLoading: isRoomsLoading } = useQuery({
    queryKey: ["floorRooms", selectedFloorId],
    queryFn: () => propertyService.getFloorRooms(selectedFloorId!),
    enabled: !!selectedFloorId,
  });

  const rooms = roomsResponse?.data || [];

  // Auto-select first room when rooms load
  useEffect(() => {
    if (rooms.length > 0) {
      const exists = rooms.some((r) => r.id === selectedRoomId);
      if (!exists) {
        setSelectedRoomId(rooms[0].id);
      }
    } else {
      setSelectedRoomId(null);
    }
  }, [rooms, selectedRoomId]);

  // 5. Fetch Beds for selected room
  const { data: bedsResponse, isLoading: isBedsLoading } = useQuery({
    queryKey: ["roomBeds", selectedRoomId],
    queryFn: () => propertyService.getRoomBeds(selectedRoomId!),
    enabled: !!selectedRoomId,
  });

  const beds = bedsResponse?.data || [];

  // 6. Fetch master list of amenities
  const { data: amenitiesResponse } = useQuery({
    queryKey: ["amenities"],
    queryFn: () => propertyService.listAmenities(),
  });

  const masterAmenities = amenitiesResponse?.data || [];

  // 7. Check if property is saved in student's wishlist
  const { data: savedQuery } = useQuery({
    queryKey: ["savedProperties"],
    queryFn: () => savedPropertyService.listSavedProperties(),
    enabled: isAuthenticated,
  });

  const isSaved = savedQuery?.data?.some((item) => item.id === id) || false;

  // 8. Fetch student's active holds
  const { data: myHoldsResponse } = useQuery({
    queryKey: ["myHolds", user?.id],
    queryFn: () => holdService.listMyHolds(),
    enabled: isAuthenticated && !!user?.id,
  });
  const myHolds = myHoldsResponse?.data || [];

  const handleToggleSave = async () => {
    if (!isAuthenticated) {
      toast.error("Please log in to save properties to your wishlist.");
      return;
    }
    if (!id) return;
    setIsSaving(true);
    try {
      if (isSaved) {
        await savedPropertyService.unsaveProperty(id);
        toast.success("Removed from wishlist.");
      } else {
        await savedPropertyService.saveProperty(id);
        toast.success("Saved to wishlist.");
      }
      queryClient.invalidateQueries({ queryKey: ["savedProperties"] });
    } catch (err) {
      toast.error("Failed to update wishlist.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleHoldBed = async (bedId: string) => {
    if (!isAuthenticated) {
      toast.error("Please log in to request a bed hold.");
      return;
    }
    
    try {
      await holdService.requestHold({ bed_id: bedId });
      toast.success("Hold requested successfully.");
      queryClient.invalidateQueries({ queryKey: ["roomBeds", selectedRoomId] });
      queryClient.invalidateQueries({ queryKey: ["studentDashboardData"] });
      queryClient.invalidateQueries({ queryKey: ["myHolds"] });
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || "Failed to request bed hold.";
      toast.error(errorMessage);
    }
  };

  if (isPropertyLoading) {
    return <PropertyDetailsSkeleton />;
  }

  if (isError || !property) {
    return (
      <div className="mx-auto max-w-md py-32 text-center px-4">
        <AlertTriangle className="mx-auto h-12 w-12 text-amber-500 mb-6" />
        <h2 className="text-3xl font-extrabold text-text tracking-tight">Property Not Found</h2>
        <p className="mt-3 text-text-secondary leading-relaxed">
          The property you are looking for does not exist or has been removed.
        </p>
        <div className="mt-8">
          <Button asChild className="h-12 px-8">
            <Link to="/properties">Back to Listings</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Deterministic Mocking of property-level amenities
  const getMockedAmenities = () => {
    if (masterAmenities.length === 0) return [];
    const ids = property.id.replace(/-/g, "");
    const selectedIndices: number[] = [];
    for (let i = 0; i < 5; i++) {
      const charCode = ids.charCodeAt(i % ids.length);
      const index = charCode % masterAmenities.length;
      if (!selectedIndices.includes(index)) {
        selectedIndices.push(index);
      }
    }
    return selectedIndices.map((idx) => masterAmenities[idx]);
  };

  const propertyAmenities = getMockedAmenities();

  return (
    <div className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8 py-8 md:py-12 w-full bg-bg text-text animate-fade-in">
      {/* Header Section */}
      <div className="mb-6 md:mb-8">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-text mb-4 leading-tight">
          {property.name}
        </h1>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-text-secondary font-medium">
            <div className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-primary shrink-0" />
              <span className="underline decoration-border underline-offset-4 hover:decoration-text transition-colors cursor-pointer">
                {property.city}, {property.state}
              </span>
            </div>
            <span className="hidden sm:inline text-border">•</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="capitalize text-xs tracking-wider font-bold bg-white shadow-sm px-2.5 py-0.5 border-border/60">
                {property.property_type}
              </Badge>
              <Badge variant="outline" className="capitalize text-xs tracking-wider font-bold bg-white shadow-sm px-2.5 py-0.5 border-border/60">
                {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
              </Badge>
              {property.is_verified && (
                <Badge variant="success" className="flex items-center gap-1 text-xs tracking-wider font-bold shadow-sm px-2.5 py-0.5">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Verified
                </Badge>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-2 h-10 px-4 rounded-xl border-border/60 shadow-sm hover:shadow-md bg-white transition-all font-semibold"
              onClick={handleToggleSave}
              disabled={isSaving}
            >
              <Heart className={`h-4 w-4 transition-colors ${isSaved ? "fill-danger text-danger" : "text-text"}`} />
              {isSaved ? "Saved" : "Save"}
            </Button>
          </div>
        </div>
      </div>

      {/* Airbnb-style Masonry Image Gallery */}
      <div className="grid grid-cols-4 grid-rows-2 gap-3 h-[300px] sm:h-[400px] lg:h-[500px] rounded-3xl overflow-hidden mb-12 shadow-sm ring-1 ring-border/30">
        {images.length > 0 ? (
          <>
            {/* Main large image */}
            <div className="col-span-4 row-span-2 sm:col-span-2 sm:row-span-2 relative cursor-pointer group bg-bg-secondary">
              <img
                src={images[activeImageIndex]?.url}
                alt={images[activeImageIndex]?.alt_text || property.name}
                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300" />
            </div>
            {/* 4 smaller images on the right (hidden on mobile) */}
            {images.slice(1, 5).map((img, idx) => (
              <div key={img.id} className="hidden sm:block relative col-span-1 row-span-1 cursor-pointer group overflow-hidden bg-bg-secondary">
                <img
                  src={img.url}
                  alt={img.alt_text || ""}
                  className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                  onClick={() => setActiveImageIndex(idx + 1)}
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300" />
              </div>
            ))}
            {/* Fallback if less than 5 images */}
            {Array.from({ length: Math.max(0, 4 - (images.length - 1)) }).map((_, i) => (
              <div key={`empty-${i}`} className="hidden sm:block relative col-span-1 row-span-1 overflow-hidden bg-bg-tertiary border border-border/20">
                <div className="flex h-full w-full items-center justify-center">
                  <ImageIcon className="h-8 w-8 text-text-tertiary/30" />
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="col-span-4 row-span-2 flex h-full w-full flex-col items-center justify-center text-text-tertiary bg-bg-tertiary">
            <Building className="h-16 w-16 stroke-[1.2] mb-3 text-text-tertiary/50" />
            <span className="text-sm font-medium">No images uploaded for this listing</span>
          </div>
        )}
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-12 lg:gap-16">
        {/* Left Column: Details */}
        <div className="space-y-12">
          {/* About Section */}
          <section>
            <h2 className="text-2xl font-bold tracking-tight mb-6">About this space</h2>
            <div className="prose prose-sm sm:prose-base prose-neutral text-text-secondary leading-relaxed whitespace-pre-wrap">
              {property.description || "No description provided for this accommodation listing."}
            </div>
          </section>

          <Separator className="bg-border/60" />

          {/* Amenities Grid */}
          <section>
            <h2 className="text-2xl font-bold tracking-tight mb-6">What this place offers</h2>
            {propertyAmenities.length === 0 ? (
              <p className="text-sm text-text-secondary">Standard PG essentials are provided.</p>
            ) : (
              <div className="grid grid-cols-2 gap-y-6 gap-x-8">
                {propertyAmenities.map((amenity) => (
                  <div key={amenity.id} className="flex items-center gap-4">
                    <div className="h-10 w-10 flex items-center justify-center rounded-xl bg-bg-secondary text-text border border-border/40">
                      {amenity.icon === "wifi" ? (
                        <Wifi className="h-5 w-5" />
                      ) : amenity.icon === "tv" ? (
                        <Tv className="h-5 w-5" />
                      ) : amenity.icon === "food" ? (
                        <Coffee className="h-5 w-5" />
                      ) : amenity.icon === "security" ? (
                        <Shield className="h-5 w-5" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5" />
                      )}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-text">{amenity.name}</span>
                      <span className="text-[11px] text-text-secondary capitalize font-medium">{amenity.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <Separator className="bg-border/60" />

          {/* ── Hierarchy Selector (Linear Style) ── */}
          <section>
            <h2 className="text-2xl font-bold tracking-tight mb-6 flex items-center gap-2">
              <BedDouble className="h-6 w-6 text-primary" />
              Select your bed
            </h2>
            
            <div className="space-y-8 bg-bg-secondary/30 p-1 rounded-3xl">
              {floors.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-border rounded-2xl bg-white shadow-sm">
                  <Layers className="mx-auto h-10 w-10 text-text-tertiary mb-3" />
                  <p className="text-sm text-text-secondary font-medium">No inventory configured for this property.</p>
                </div>
              ) : (
                <>
                  {/* Floor Level Selector */}
                  <div className="space-y-4">
                    <div className="flex flex-wrap gap-2">
                      {floors.map((floor) => (
                        <button
                          key={floor.id}
                          onClick={() => {
                            setSelectedFloorId(floor.id);
                            setSelectedRoomId(null);
                          }}
                          className={`px-6 py-3 rounded-xl text-sm font-bold transition-all duration-300 cursor-pointer border ${
                            selectedFloorId === floor.id
                              ? "bg-text text-bg border-text shadow-md scale-100"
                              : "bg-white text-text-secondary border-border/60 hover:border-text/30 hover:text-text hover:bg-bg-secondary"
                          }`}
                        >
                          {floor.name || `Floor ${floor.floor_number}`}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Room Level Selector */}
                  <div className="space-y-4 pt-2">
                    {isRoomsLoading ? (
                      <div className="flex justify-center items-center py-10">
                        <LoadingSpinner size="md" />
                      </div>
                    ) : rooms.length === 0 ? (
                      <p className="text-sm text-text-tertiary italic p-6 bg-white rounded-xl border border-border/40">No rooms listed on this floor.</p>
                    ) : (
                      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2">
                        {rooms.map((room) => (
                          <RoomCard
                            key={room.id}
                            room={room}
                            isSelected={selectedRoomId === room.id}
                            onClick={() => setSelectedRoomId(room.id)}
                          />
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Bed Level Details */}
                  {selectedRoomId && (
                    <div className="space-y-4 pt-6 mt-4 border-t border-border/60">
                      {isBedsLoading ? (
                        <div className="flex justify-center items-center py-8">
                          <LoadingSpinner size="md" />
                        </div>
                      ) : beds.length === 0 ? (
                        <p className="text-sm text-text-tertiary italic">No beds configured for this room.</p>
                      ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                          {beds.map((bed) => {
                            const myActiveHold = myHolds.find(
                              (h) => h.bed_id === bed.id && (h.status === HoldStatus.PENDING || h.status === HoldStatus.APPROVED)
                            );

                            return (
                              <BedCard
                                key={bed.id}
                                bed={bed}
                                myActiveHold={myActiveHold}
                                onHoldRequest={handleHoldBed}
                                isHolding={false}
                              />
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </section>

          {property.rules && (
            <>
              <Separator className="bg-border/60" />
              <section>
                <h2 className="text-2xl font-bold tracking-tight mb-6">House Rules</h2>
                <div className="p-6 rounded-2xl bg-bg-secondary border border-border/60">
                  <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                    {property.rules}
                  </p>
                </div>
              </section>
            </>
          )}
        </div>

        {/* Right Column: Floating Booking Sidebar */}
        <div className="relative">
          <div className="sticky top-28 space-y-6">
            {/* Reservation Card (Airbnb / Stripe style) */}
            <Card className="border-0 bg-white shadow-[0_8px_30px_rgb(0,0,0,0.08)] ring-1 ring-border/40 rounded-3xl overflow-hidden">
              <CardContent className="p-8 space-y-8">
                <div className="flex flex-col">
                  <span className="text-[13px] font-bold tracking-wider uppercase text-text-secondary mb-2">Monthly Rent</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-extrabold text-text tracking-tight">
                      {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
                    </span>
                    <span className="text-base font-medium text-text-secondary">/ mo</span>
                  </div>
                </div>

                <div className="space-y-3 bg-bg-secondary/50 p-5 rounded-2xl border border-border/40">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-text-secondary font-medium">Availability</span>
                    <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded text-xs">{property.available_beds} beds left</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-text-secondary font-medium">Total Capacity</span>
                    <span className="font-semibold text-text">{property.total_beds} beds</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <Button 
                    className="w-full h-14 text-base font-bold rounded-xl shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all hover:-translate-y-0.5 active:translate-y-0"
                    onClick={() => {
                      document.getElementById('bed-selection-section')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    Select a Bed
                  </Button>
                  <p className="text-[11px] text-center text-text-tertiary font-medium">
                    You won't be charged yet
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Contact Details Card */}
            <Card className="border-0 bg-white shadow-sm ring-1 ring-border/40 rounded-2xl overflow-hidden">
              <CardContent className="p-6 space-y-5">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="h-5 w-5 text-primary" />
                  <h3 className="font-bold text-text">Contact Manager</h3>
                </div>
                
                {isAuthenticated ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-bg-secondary border border-border flex items-center justify-center">
                        <Phone className="h-4 w-4 text-text-secondary" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[11px] uppercase tracking-wider text-text-tertiary font-bold">Phone</span>
                        <a href={`tel:${property.contact_phone}`} className="text-sm font-semibold hover:text-primary transition-colors">
                          {property.contact_phone || "Not Provided"}
                        </a>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-bg-secondary border border-border flex items-center justify-center">
                        <Mail className="h-4 w-4 text-text-secondary" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[11px] uppercase tracking-wider text-text-tertiary font-bold">Email</span>
                        <a href={`mailto:${property.contact_email}`} className="text-sm font-semibold hover:text-primary transition-colors">
                          {property.contact_email || "Not Provided"}
                        </a>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-bg-secondary border border-border/60 p-5 rounded-xl text-center space-y-4">
                    <p className="text-xs text-text-secondary font-medium">
                      Contact details are locked for guests to prevent spam.
                    </p>
                    <Button size="sm" variant="default" asChild className="w-full h-10 rounded-lg">
                      <Link to="/login">Sign in to view</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
