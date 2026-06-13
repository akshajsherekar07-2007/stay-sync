import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft,
  Heart,
  MapPin,
  Building,
  Phone,
  Mail,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Bed,
  Layers,
  Sparkles,
  Wifi,
  Tv,
  Coffee,
  Shield,
  Clock
} from "lucide-react";

import { useAuthStore } from "../../../stores/authStore";
import { propertyService } from "../../../services/propertyService";
import { savedPropertyService } from "../../../services/savedPropertyService";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { Separator } from "../../../components/ui/Separator";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function PropertyDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuthStore();

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
      // If selectedRoomId is null or not in the currently loaded rooms, select the first one
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

  const handleHoldBed = (bedNumber: string) => {
    if (!isAuthenticated) {
      toast.error("Please log in to request a bed hold.");
      return;
    }
    toast.info(`Hold request for Bed ${bedNumber} is a Phase 2 feature!`);
  };

  if (isPropertyLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !property) {
    return (
      <div className="mx-auto max-w-md py-20 text-center px-4">
        <AlertTriangle className="mx-auto h-12 w-12 text-amber-500 mb-4" />
        <h2 className="text-2xl font-bold text-text">Property Not Found</h2>
        <p className="mt-2 text-text-secondary">
          The property you are looking for does not exist or has been removed.
        </p>
        <div className="mt-6">
          <Button asChild>
            <Link to="/properties">Back to Listings</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Deterministic Mocking of property-level amenities since they are not returned in the API
  // Using the property ID string to pick 4-5 amenities from the master list
  const getMockedAmenities = () => {
    if (masterAmenities.length === 0) return [];
    // Standard amenities to prefer
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
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 w-full bg-bg text-text">
      {/* Back to Browse */}
      <Link
        to="/properties"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary hover:text-primary transition-colors mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Listings
      </Link>

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <Badge variant="outline" className="capitalize border-primary/30 text-primary bg-primary/5">
              {property.property_type}
            </Badge>
            <Badge className="capitalize bg-neutral-900 dark:bg-neutral-800 text-white">
              {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
            </Badge>
            {property.is_verified && (
              <Badge variant="success" className="flex items-center gap-0.5 text-white">
                <ShieldCheck className="h-3 w-3" />
                Verified Stay
              </Badge>
            )}
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">{property.name}</h1>
          <div className="flex items-center gap-1 text-sm text-text-secondary mt-2">
            <MapPin className="h-4 w-4 text-primary shrink-0" />
            <span>
              {property.address_line1}
              {property.address_line2 ? `, ${property.address_line2}` : ""}
              , {property.city}, {property.state} - {property.pincode}
            </span>
          </div>
        </div>

        {/* Share and Wishlist quick actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="default"
            className="flex items-center gap-1.5"
            onClick={handleToggleSave}
            disabled={isSaving}
          >
            <Heart className={`h-4 w-4 ${isSaved ? "fill-danger text-danger" : "text-text-secondary"}`} />
            {isSaved ? "Saved" : "Save Stay"}
          </Button>
        </div>
      </div>

      {/* Main Grid: Visuals & Info / Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Image Gallery, Description, Amenities, Hierarchy */}
        <div className="lg:col-span-2 space-y-8">
          {/* Image Gallery */}
          <div className="space-y-3">
            <div className="relative aspect-video rounded-xl overflow-hidden bg-bg-tertiary border border-border">
              {images.length > 0 ? (
                <img
                  src={images[activeImageIndex]?.url}
                  alt={images[activeImageIndex]?.alt_text || property.name}
                  className="h-full w-full object-cover transition-opacity duration-300"
                />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center text-text-tertiary">
                  <Building className="h-20 w-20 stroke-[1.2]" />
                  <span className="text-sm mt-3">No images uploaded for this listing</span>
                </div>
              )}
            </div>

            {images.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
                {images.map((img, idx) => (
                  <button
                    key={img.id}
                    onClick={() => setActiveImageIndex(idx)}
                    className={`relative w-24 aspect-[16/10] rounded-lg overflow-hidden shrink-0 border-2 transition-all cursor-pointer ${
                      activeImageIndex === idx ? "border-primary scale-[0.98]" : "border-border hover:border-text-secondary"
                    }`}
                  >
                    <img src={img.url} alt={img.alt_text || ""} className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Description & Rules */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-lg font-bold">About this accommodation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
                {property.description || "No description provided for this accommodation listing."}
              </p>

              {property.rules && (
                <>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-bold text-text mb-2">House Rules</h4>
                    <p className="text-text-secondary text-xs leading-relaxed whitespace-pre-wrap">
                      {property.rules}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Amenities Grid */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                Featured Amenities
              </CardTitle>
            </CardHeader>
            <CardContent>
              {propertyAmenities.length === 0 ? (
                <p className="text-xs text-text-tertiary">Standard PG essentials are provided.</p>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {propertyAmenities.map((amenity) => (
                    <div key={amenity.id} className="flex items-center gap-2.5 p-3 rounded-lg bg-bg-secondary border border-border/60">
                      <div className="h-8 w-8 flex items-center justify-center rounded-md bg-primary/10 text-primary">
                        {amenity.icon === "wifi" ? (
                          <Wifi className="h-4 w-4" />
                        ) : amenity.icon === "tv" ? (
                          <Tv className="h-4 w-4" />
                        ) : amenity.icon === "food" ? (
                          <Coffee className="h-4 w-4" />
                        ) : amenity.icon === "security" ? (
                          <Shield className="h-4 w-4" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4" />
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-semibold truncate text-text">{amenity.name}</span>
                        <span className="text-[9px] text-text-secondary capitalize">{amenity.category}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── Floor / Room / Bed Hierarchy Selector ── */}
          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="border-b border-border pb-4">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg font-bold">Room & Bed Availability</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {floors.length === 0 ? (
                <div className="text-center py-10 border border-dashed border-border rounded-lg bg-bg-secondary">
                  <Layers className="mx-auto h-8 w-8 text-text-tertiary mb-2" />
                  <p className="text-sm text-text-secondary">No inventory configuration found for this property.</p>
                </div>
              ) : (
                <>
                  {/* Floor Level Selector */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary">Select Floor:</span>
                    <div className="flex flex-wrap gap-2">
                      {floors.map((floor) => (
                        <button
                          key={floor.id}
                          onClick={() => {
                            setSelectedFloorId(floor.id);
                            setSelectedRoomId(null);
                          }}
                          className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                            selectedFloorId === floor.id
                              ? "bg-primary text-primary-foreground border-primary shadow-xs"
                              : "bg-bg border-border hover:border-text-secondary text-text"
                          }`}
                        >
                          {floor.name || `Floor ${floor.floor_number}`}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Room Level Selector */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-text-secondary">Select Room:</span>
                    {isRoomsLoading ? (
                      <div className="flex justify-center items-center py-6">
                        <LoadingSpinner size="sm" />
                      </div>
                    ) : rooms.length === 0 ? (
                      <p className="text-xs text-text-tertiary italic">No rooms listed on this floor.</p>
                    ) : (
                      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
                        {rooms.map((room) => (
                          <button
                            key={room.id}
                            onClick={() => setSelectedRoomId(room.id)}
                            className={`p-3.5 rounded-lg border text-left transition-all flex flex-col justify-between cursor-pointer ${
                              selectedRoomId === room.id
                                ? "bg-primary/5 border-primary shadow-xs ring-1 ring-primary/30"
                                : "bg-bg border-border hover:border-text-secondary"
                            }`}
                          >
                            <div>
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-bold text-text">Room {room.room_number}</span>
                                <Badge variant="outline" className="text-[10px] capitalize py-0">
                                  {room.sharing_type} Share
                                </Badge>
                              </div>
                              <p className="text-[11px] text-text-secondary line-clamp-1">
                                {room.name || "Standard Student Room"}
                              </p>
                            </div>
                            <div className="flex justify-between items-end mt-4 pt-2 border-t border-border/50 w-full text-xs">
                              <span className="text-[10px] text-text-secondary">Rent / Bed</span>
                              <span className="font-bold text-primary">₹{room.price_per_bed.toLocaleString("en-IN")}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Bed Level Details */}
                  {selectedRoomId && (
                    <div className="space-y-3 pt-4 border-t border-border">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-text-secondary">Beds inside selected Room:</span>
                        <div className="flex items-center gap-3 text-[10px] text-text-secondary">
                          <span className="flex items-center gap-1">
                            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Vacant
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="h-2 w-2 rounded-full bg-amber-500" /> Held
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="h-2 w-2 rounded-full bg-rose-500" /> Occupied
                          </span>
                        </div>
                      </div>

                      {isBedsLoading ? (
                        <div className="flex justify-center items-center py-6">
                          <LoadingSpinner size="sm" />
                        </div>
                      ) : beds.length === 0 ? (
                        <p className="text-xs text-text-tertiary italic">No beds configured for this room.</p>
                      ) : (
                        <div className="grid gap-3 sm:grid-cols-2">
                          {beds.map((bed) => {
                            const isVacant = bed.status === "vacant";
                            const isHeld = bed.status === "held";

                            return (
                              <div
                                key={bed.id}
                                className={`flex items-center justify-between p-4 rounded-lg border bg-bg/50 ${
                                  isVacant
                                    ? "border-emerald-500/20 hover:bg-emerald-500/5"
                                    : isHeld
                                    ? "border-amber-500/20"
                                    : "border-rose-500/20 opacity-70"
                                }`}
                              >
                                <div className="flex items-center gap-3">
                                  <div
                                    className={`h-8 w-8 flex items-center justify-center rounded-md ${
                                      isVacant
                                        ? "bg-emerald-500/10 text-emerald-600"
                                        : isHeld
                                        ? "bg-amber-500/10 text-amber-600"
                                        : "bg-rose-500/10 text-rose-600"
                                    }`}
                                  >
                                    <Bed className="h-4.5 w-4.5" />
                                  </div>
                                  <div className="flex flex-col">
                                    <span className="text-xs font-bold text-text">Bed {bed.bed_number}</span>
                                    <span className="text-[10px] text-text-secondary">
                                      {bed.label || "Regular Bed"}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className="text-xs font-semibold text-text">
                                    {bed.price ? `₹${bed.price.toLocaleString("en-IN")}` : "Included"}
                                  </span>
                                  {isVacant ? (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="border-emerald-500 text-emerald-600 hover:bg-emerald-500 hover:text-white text-[10px] py-1 h-7 px-2.5 font-semibold cursor-pointer"
                                      onClick={() => handleHoldBed(bed.bed_number)}
                                    >
                                      Hold Bed
                                    </Button>
                                  ) : (
                                    <Badge
                                      variant={isHeld ? "warning" : "destructive"}
                                      className="text-[9px] py-0.5 px-2 capitalize text-white"
                                    >
                                      {bed.status}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Column: Side Booking Info, Contact Owner, and Login CTA */}
        <div className="space-y-6">
          {/* Reservation Card */}
          <Card className="border-border bg-card shadow-md">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-base font-bold">Pricing details</CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div>
                <span className="text-xs text-text-secondary block mb-1">Monthly Rent Range</span>
                <span className="text-3xl font-extrabold text-primary tracking-tight">
                  {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}{" "}
                  {property.max_price && property.max_price !== property.min_price ? (
                    <span className="text-xl font-normal text-text-secondary">
                      - ₹{property.max_price.toLocaleString("en-IN")}
                    </span>
                  ) : (
                    ""
                  )}
                  <span className="text-xs font-normal text-text-secondary"> / month</span>
                </span>
              </div>

              <div className="space-y-3 bg-bg-secondary p-4 rounded-xl border border-border text-xs">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Vacant Beds:</span>
                  <span className="font-bold text-emerald-600">{property.available_beds} beds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Total Beds:</span>
                  <span className="font-semibold text-text">{property.total_beds} beds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Verification Status:</span>
                  <span className="font-bold text-emerald-600">{property.is_verified ? "Verified" : "Pending"}</span>
                </div>
              </div>

              {/* Save/Contact Owner Block */}
              <div className="space-y-2">
                <Button className="w-full font-bold flex items-center justify-center gap-1.5 h-11" onClick={handleToggleSave}>
                  <Heart className={`h-4.5 w-4.5 ${isSaved ? "fill-white" : ""}`} />
                  {isSaved ? "Remove from Wishlist" : "Add to Wishlist"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Contact Details Card */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-1.5 text-text-secondary">
                <Clock className="h-4 w-4" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isAuthenticated ? (
                <div className="space-y-3 text-xs">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-primary shrink-0" />
                    <a href={`tel:${property.contact_phone}`} className="font-semibold hover:underline text-text">
                      {property.contact_phone || "Not Provided"}
                    </a>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-primary shrink-0" />
                    <a href={`mailto:${property.contact_email}`} className="font-semibold hover:underline text-text">
                      {property.contact_email || "Not Provided"}
                    </a>
                  </div>
                </div>
              ) : (
                <div className="bg-bg-secondary border border-border p-4 rounded-lg text-center space-y-3">
                  <p className="text-xs text-text-secondary">
                    Contact details and specific address directions are locked for guests.
                  </p>
                  <Button size="sm" variant="outline" asChild className="w-full">
                    <Link to="/login">Reveal Details</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Guest Login CTA Banner */}
          {!isAuthenticated && (
            <div className="rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20 p-5 space-y-4">
              <h3 className="text-sm font-extrabold text-primary flex items-center gap-1.5">
                <Building className="h-4 w-4" />
                Join StaySync to book
              </h3>
              <p className="text-[11px] text-text-secondary leading-relaxed">
                StaySync accounts allow you to reserve live bed holds, receive custom real-time alerts, and easily map accommodation coordinates.
              </p>
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Button size="sm" asChild>
                  <Link to="/login">Sign In</Link>
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <Link to="/register">Register</Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
