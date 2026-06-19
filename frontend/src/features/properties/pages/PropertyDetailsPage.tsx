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
import styles from "./PropertyDetailsPage.module.css";

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
      <div className={styles.errorState}>
        <AlertTriangle className={styles.errorIcon} />
        <h2 className={styles.errorTitle}>Property Not Found</h2>
        <p className={styles.errorDesc}>
          The property you are looking for does not exist or has been removed.
        </p>
        <div className={styles.errorAction}>
          <Button asChild className={styles.errorBtn}>
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
    <div className={styles.container}>
      {/* Header Section */}
      <div className={styles.header}>
        <h1 className={styles.title}>
          {property.name}
        </h1>
        <div className={styles.headerMeta}>
          <div className={styles.metaInfo}>
            <div className={styles.location}>
              <MapPin className={styles.locationIcon} />
              <span className={styles.locationText}>
                {property.city}, {property.state}
              </span>
            </div>
            <span className={styles.metaDot}>•</span>
            <div className={styles.badges}>
              <Badge variant="outline" className={styles.badge}>
                {property.property_type}
              </Badge>
              <Badge variant="outline" className={styles.badge}>
                {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
              </Badge>
              {property.is_verified && (
                <Badge variant="success" className={styles.verifiedBadge}>
                  <ShieldCheck className={styles.verifiedIcon} />
                  Verified
                </Badge>
              )}
            </div>
          </div>
          
          <div className={styles.actions}>
            <Button
              variant="outline"
              size="sm"
              className={styles.saveBtn}
              onClick={handleToggleSave}
              disabled={isSaving}
            >
              <Heart className={`${styles.saveIcon} ${isSaved ? styles.saveIconSaved : ""}`} />
              {isSaved ? "Saved" : "Save"}
            </Button>
          </div>
        </div>
      </div>

      {/* Airbnb-style Masonry Image Gallery */}
      <div className={styles.gallery}>
        {images.length > 0 ? (
          <>
            {/* Main large image */}
            <div className={styles.mainImageWrapper}>
              <img
                src={images[activeImageIndex]?.url}
                alt={images[activeImageIndex]?.alt_text || property.name}
                className={styles.galleryImage}
              />
              <div className={styles.imageOverlay} />
            </div>
            {/* 4 smaller images on the right (hidden on mobile) */}
            {images.slice(1, 5).map((img, idx) => (
              <div key={img.id} className={styles.subImageWrapper} onClick={() => setActiveImageIndex(idx + 1)}>
                <img
                  src={img.url}
                  alt={img.alt_text || ""}
                  className={styles.galleryImage}
                />
                <div className={styles.imageOverlay} />
              </div>
            ))}
            {/* Fallback if less than 5 images */}
            {Array.from({ length: Math.max(0, 4 - (images.length - 1)) }).map((_, i) => (
              <div key={`empty-${i}`} className={styles.emptySubImage}>
                <div className={styles.emptySubIconWrapper}>
                  <ImageIcon className={styles.emptySubIcon} />
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className={styles.noImagesWrapper}>
            <Building className={styles.noImagesIcon} />
            <span className={styles.noImagesText}>No images uploaded for this listing</span>
          </div>
        )}
      </div>

      {/* Main Content Layout */}
      <div className={styles.contentLayout}>
        {/* Left Column: Details */}
        <div className={styles.leftColumn}>
          {/* About Section */}
          <section>
            <h2 className={styles.sectionTitle}>About this space</h2>
            <div className={styles.description}>
              {property.description || "No description provided for this accommodation listing."}
            </div>
          </section>

          <Separator className="bg-border/60" />

          {/* Amenities Grid */}
          <section>
            <h2 className={styles.sectionTitle}>What this place offers</h2>
            {propertyAmenities.length === 0 ? (
              <p className={styles.description}>Standard PG essentials are provided.</p>
            ) : (
              <div className={styles.amenitiesGrid}>
                {propertyAmenities.map((amenity) => (
                  <div key={amenity.id} className={styles.amenityItem}>
                    <div className={styles.amenityIconWrapper}>
                      {amenity.icon === "wifi" ? (
                        <Wifi className={styles.amenityIcon} />
                      ) : amenity.icon === "tv" ? (
                        <Tv className={styles.amenityIcon} />
                      ) : amenity.icon === "food" ? (
                        <Coffee className={styles.amenityIcon} />
                      ) : amenity.icon === "security" ? (
                        <Shield className={styles.amenityIcon} />
                      ) : (
                        <CheckCircle2 className={styles.amenityIcon} />
                      )}
                    </div>
                    <div className={styles.amenityTextWrapper}>
                      <span className={styles.amenityName}>{amenity.name}</span>
                      <span className={styles.amenityCategory}>{amenity.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <Separator className="bg-border/60" />

          {/* ── Hierarchy Selector (Linear Style) ── */}
          <section id="bed-selection-section">
            <h2 className={styles.sectionTitle}>
              <BedDouble className="h-6 w-6 text-primary" />
              Select your bed
            </h2>
            
            <div className={styles.selectorContainer}>
              {floors.length === 0 ? (
                <div className={styles.emptyFloors}>
                  <Layers className={styles.emptyFloorsIcon} />
                  <p className={styles.emptyFloorsText}>No inventory configured for this property.</p>
                </div>
              ) : (
                <>
                  {/* Floor Level Selector */}
                  <div>
                    <div className={styles.floorTabs}>
                      {floors.map((floor) => (
                        <button
                          key={floor.id}
                          onClick={() => {
                            setSelectedFloorId(floor.id);
                            setSelectedRoomId(null);
                          }}
                          className={`${styles.floorTab} ${selectedFloorId === floor.id ? styles.floorTabActive : styles.floorTabInactive}`}
                        >
                          {floor.name || `Floor ${floor.floor_number}`}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Room Level Selector */}
                  <div className={styles.roomsContainer}>
                    {isRoomsLoading ? (
                      <div className={styles.loadingSpinner}>
                        <LoadingSpinner size="md" />
                      </div>
                    ) : rooms.length === 0 ? (
                      <p className={styles.emptyRooms}>No rooms listed on this floor.</p>
                    ) : (
                      <div className={styles.roomsGrid}>
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
                    <div className={styles.bedsContainer}>
                      {isBedsLoading ? (
                        <div className={styles.loadingSpinner}>
                          <LoadingSpinner size="md" />
                        </div>
                      ) : beds.length === 0 ? (
                        <p className={styles.emptyRooms}>No beds configured for this room.</p>
                      ) : (
                        <div className={styles.bedsGrid}>
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
                <h2 className={styles.sectionTitle}>House Rules</h2>
                <div className={styles.rulesCard}>
                  <p className={styles.rulesText}>
                    {property.rules}
                  </p>
                </div>
              </section>
            </>
          )}
        </div>

        {/* Right Column: Floating Booking Sidebar */}
        <div className={styles.sidebar}>
          <div className={styles.sidebarSticky}>
            {/* Reservation Card (Airbnb / Stripe style) */}
            <Card className={styles.bookingCard}>
              <CardContent className={styles.bookingContent}>
                <div>
                  <span className={styles.priceLabel}>Monthly Rent</span>
                  <div className={styles.priceWrapper}>
                    <span className={styles.priceAmount}>
                      {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
                    </span>
                    <span className={styles.priceUnit}>/ mo</span>
                  </div>
                </div>

                <div className={styles.statsBox}>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Availability</span>
                    <span className={styles.statValueAvailable}>{property.available_beds} beds left</span>
                  </div>
                  <div className={styles.statRow}>
                    <span className={styles.statLabel}>Total Capacity</span>
                    <span className={styles.statValueTotal}>{property.total_beds} beds</span>
                  </div>
                </div>

                <div className={styles.bookingAction}>
                  <Button 
                    className={styles.selectBedBtn}
                    onClick={() => {
                      document.getElementById('bed-selection-section')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    Select a Bed
                  </Button>
                  <p className={styles.bookingNotice}>
                    You won't be charged yet
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Contact Details Card */}
            <Card className={styles.contactCard}>
              <CardContent className={styles.contactContent}>
                <div className={styles.contactTitle}>
                  <Clock className={styles.contactTitleIcon} />
                  <h3 className={styles.contactTitleText}>Contact Manager</h3>
                </div>
                
                {isAuthenticated ? (
                  <div className={styles.contactList}>
                    <div className={styles.contactItem}>
                      <div className={styles.contactIconWrapper}>
                        <Phone className={styles.contactIcon} />
                      </div>
                      <div className={styles.contactTextWrapper}>
                        <span className={styles.contactLabel}>Phone</span>
                        <a href={`tel:${property.contact_phone}`} className={styles.contactLink}>
                          {property.contact_phone || "Not Provided"}
                        </a>
                      </div>
                    </div>
                    <div className={styles.contactItem}>
                      <div className={styles.contactIconWrapper}>
                        <Mail className={styles.contactIcon} />
                      </div>
                      <div className={styles.contactTextWrapper}>
                        <span className={styles.contactLabel}>Email</span>
                        <a href={`mailto:${property.contact_email}`} className={styles.contactLink}>
                          {property.contact_email || "Not Provided"}
                        </a>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={styles.contactLocked}>
                    <p className={styles.contactLockedText}>
                      Contact details are locked for guests to prevent spam.
                    </p>
                    <Button size="sm" variant="default" asChild className={styles.contactLockedBtn}>
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
