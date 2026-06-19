import { useState, useEffect } from "react";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Building2,
  MapPin,
  Home,
  Building,
  Hotel,
  Users,
  User,
  AlignLeft,
  ClipboardList,
  Globe2,
  Save,
  ArrowLeft,
  ArrowRight,
  Plus,
  Trash2,
  Star,
  Upload,
  CheckCircle2,
  Sparkles,
  Layers,
  Bed
} from "lucide-react";

import { ownerPropertyService } from "../../../services/ownerPropertyService";
import { propertyService } from "../../../services/propertyService";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../../components/ui/Card";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Button } from "../../../components/ui/Button";
import { PropertyType, GenderPreference, SharingType } from "../../../types/enums";
import { propertyWizardSchema, type PropertyWizardInput } from "../schemas/propertySchema";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

interface PropertyFormProps {
  propertyId?: string;
  initialData?: {
    property: any;
    images: any[];
    floors: any[];
  };
  initialStep?: number;
}

export default function PropertyForm({ propertyId: propIdFromProps, initialData, initialStep = 1 }: PropertyFormProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setSearchParams = useSearchParams()[1];

  // Active property ID (starts empty in create mode, populated after Step 1 create)
  const [propertyId, setPropertyId] = useState<string | undefined>(propIdFromProps);
  const [currentStep, setCurrentStep] = useState<number>(initialStep);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);

  // Tracks removed entities so we can delete them from backend on Step 3 submit
  const [deletedFloorIds, setDeletedFloorIds] = useState<string[]>([]);
  const [deletedRoomIds, setDeletedRoomIds] = useState<string[]>([]);
  const [deletedBedIds, setDeletedBedIds] = useState<string[]>([]);

  // 1. Fetch master catalog of amenities
  const { data: amenitiesCatalogResponse } = useQuery({
    queryKey: ["amenities"],
    queryFn: () => propertyService.listAmenities(),
  });
  const masterAmenities = amenitiesCatalogResponse?.data || [];

  // Determine which amenities are initially attached
  // We use the deterministic mocking function matching the details page
  const getMockedAmenities = (id: string) => {
    if (masterAmenities.length === 0) return [];
    const ids = id.replace(/-/g, "");
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

  const initialAmenities = propertyId ? getMockedAmenities(propertyId) : [];

  // 2. Fetch images query (keeps images updated in Step 2)
  const { data: imagesResponse, refetch: refetchImages } = useQuery({
    queryKey: ["propertyImages", propertyId],
    queryFn: () => propertyService.getPropertyImages(propertyId!),
    enabled: !!propertyId,
  });
  const propertyImages = imagesResponse?.data || initialData?.images || [];

  // React Hook Form Instance
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    control,
    reset,
    trigger,
    getValues,
    formState: { errors },
  } = useForm<PropertyWizardInput>({
    resolver: zodResolver(propertyWizardSchema),
    defaultValues: {
      name: initialData?.property?.name || "",
      description: initialData?.property?.description || "",
      property_type: initialData?.property?.property_type || PropertyType.PG,
      gender_preference: initialData?.property?.gender_preference || GenderPreference.COED,
      address_line1: initialData?.property?.address_line1 || "",
      address_line2: initialData?.property?.address_line2 || "",
      city: initialData?.property?.city || "",
      state: initialData?.property?.state || "",
      pincode: initialData?.property?.pincode || "",
      country: initialData?.property?.country || "India",
      latitude: initialData?.property?.latitude || null,
      longitude: initialData?.property?.longitude || null,
      google_place_id: initialData?.property?.google_place_id || "",
      place_name: initialData?.property?.place_name || "",
      rules: initialData?.property?.rules || "",
      amenities: initialAmenities.map((a: any) => a.id),
      floors: initialData?.floors || [],
    },
  });

  const selectedType = watch("property_type");
  const selectedGender = watch("gender_preference");
  const formAmenities = watch("amenities") || [];

  // Reset form when initialData becomes available (Edit pre-population)
  useEffect(() => {
    if (initialData) {
      setPropertyId(initialData.property.id);
      reset({
        name: initialData.property.name || "",
        description: initialData.property.description || "",
        property_type: initialData.property.property_type as PropertyType,
        gender_preference: initialData.property.gender_preference as GenderPreference,
        address_line1: initialData.property.address_line1 || "",
        address_line2: initialData.property.address_line2 || "",
        city: initialData.property.city || "",
        state: initialData.property.state || "",
        pincode: initialData.property.pincode || "",
        country: initialData.property.country || "India",
        latitude: initialData.property.latitude || null,
        longitude: initialData.property.longitude || null,
        google_place_id: initialData.property.google_place_id || "",
        place_name: initialData.property.place_name || "",
        rules: initialData.property.rules || "",
        amenities: getMockedAmenities(initialData.property.id).map((a: any) => a.id),
        floors: initialData.floors || [],
      });
    }
  }, [initialData, reset]);

  // Synchronize search params step value
  useEffect(() => {
    if (initialStep !== currentStep) {
      setCurrentStep(initialStep);
    }
  }, [initialStep]);

  const changeStep = (step: number) => {
    setCurrentStep(step);
    setSearchParams({ step: step.toString() });
  };

  // Stepper Header click handler (Edit mode only)
  const handleStepClick = async (step: number) => {
    if (!propertyId) return; // Block step clicks in new listing creation until created
    
    // Validate current step before transitioning
    if (currentStep === 1) {
      const isValid = await trigger([
        "name",
        "property_type",
        "gender_preference",
        "address_line1",
        "city",
        "state",
        "pincode",
      ]);
      if (!isValid) {
        toast.error("Please resolve validation errors in Step 1.");
        return;
      }
    }
    changeStep(step);
  };

  // Step 1: General Details submission
  const handleSaveStep1 = async (data: PropertyWizardInput) => {
    setIsSubmitting(true);
    try {
      const payload = {
        name: data.name,
        description: data.description || null,
        property_type: data.property_type,
        gender_preference: data.gender_preference,
        address_line1: data.address_line1,
        address_line2: data.address_line2 || null,
        city: data.city,
        state: data.state,
        pincode: data.pincode,
        country: data.country || "India",
        latitude: data.latitude === "" || data.latitude === null || data.latitude === undefined ? null : Number(data.latitude),
        longitude: data.longitude === "" || data.longitude === null || data.longitude === undefined ? null : Number(data.longitude),
        google_place_id: data.google_place_id || null,
        place_name: data.place_name || null,
        rules: data.rules || null,
      };

      if (propertyId) {
        // PATCH Update
        const response = await ownerPropertyService.updateProperty(propertyId, payload);
        if (response.success) {
          toast.success("General details updated.");
          changeStep(2);
        }
      } else {
        // POST Create
        const response = await ownerPropertyService.createProperty(payload);
        if (response.success) {
          toast.success("Listing initialized successfully!");
          setPropertyId(response.data.id);
          queryClient.invalidateQueries({ queryKey: ["ownedProperties"] });
          // Redirect to the edit wizard step 2
          navigate(`/owner/properties/${response.data.id}/edit?step=2`, { replace: true });
        }
      }
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Failed to save details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2: Media & Amenities Save
  const handleSaveStep2 = async () => {
    if (!propertyId) return;
    setIsSubmitting(true);
    try {
      // Synchronize amenities checklist in database
      // 1. Attach checked amenities (duplicates skipped silently on backend)
      if (formAmenities.length > 0) {
        await ownerPropertyService.attachAmenities(propertyId, {
          amenity_ids: formAmenities,
        });
      }

      // 2. Detach deselected ones
      // Since details mocks them initially, we only detach if they were mocked but now deselected
      const mockedIds = initialAmenities.map((a) => a.id);
      const deselectedIds = mockedIds.filter((id) => !formAmenities.includes(id));
      for (const aid of deselectedIds) {
        try {
          await ownerPropertyService.detachAmenity(propertyId, aid);
        } catch (e) {
          // Ignore if not attached in real DB
        }
      }

      toast.success("Media & Amenities saved.");
      changeStep(3);
    } catch (err: any) {
      toast.error("Failed to save configuration.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 3: Inventory Save & Sync
  const handleSaveStep3 = async (floorsData: any[]) => {
    if (!propertyId) return;
    setIsSubmitting(true);
    try {
      // 1. Deletions (Beds → Rooms → Floors order)
      for (const bid of deletedBedIds) {
        try {
          await ownerPropertyService.deleteBed(bid);
        } catch (e: any) {
          if (e.response?.status !== 404) throw e;
        }
      }
      setDeletedBedIds([]);

      for (const rid of deletedRoomIds) {
        try {
          await ownerPropertyService.deleteRoom(rid);
        } catch (e: any) {
          if (e.response?.status !== 404) throw e;
        }
      }
      setDeletedRoomIds([]);

      for (const fid of deletedFloorIds) {
        try {
          await ownerPropertyService.deleteFloor(fid);
        } catch (e: any) {
          if (e.response?.status !== 404) throw e;
        }
      }
      setDeletedFloorIds([]);

      // 2. Cascaded Synchronization of Floors, Rooms, and Beds
      for (let fIdx = 0; fIdx < floorsData.length; fIdx++) {
        const floor = floorsData[fIdx];
        const floorPayload = {
          floor_number: Number(floor.floor_number),
          name: floor.name || `Floor ${floor.floor_number}`,
          description: floor.description || "",
          sort_order: fIdx,
        };

        let resolvedFloorId = floor.id;
        if (resolvedFloorId) {
          await ownerPropertyService.updateFloor(resolvedFloorId, floorPayload);
        } else {
          const res = await ownerPropertyService.createFloor(propertyId, floorPayload);
          resolvedFloorId = res.data.id;
        }

        // Rooms
        const rooms = floor.rooms || [];
        for (let rIdx = 0; rIdx < rooms.length; rIdx++) {
          const room = rooms[rIdx];
          const roomPayload = {
            room_number: room.room_number,
            name: room.name || "",
            sharing_type: room.sharing_type,
            price_per_bed: Number(room.price_per_bed),
            description: room.description || "",
            has_attached_bath: !!room.has_attached_bath,
            has_ac: !!room.has_ac,
            has_balcony: !!room.has_balcony,
            sort_order: rIdx,
          };

          let resolvedRoomId = room.id;
          if (resolvedRoomId) {
            await ownerPropertyService.updateRoom(resolvedRoomId, roomPayload);
          } else {
            const res = await ownerPropertyService.createRoom(resolvedFloorId, roomPayload);
            resolvedRoomId = res.data.id;
          }

          // Beds
          const beds = room.beds || [];
          for (let bIdx = 0; bIdx < beds.length; bIdx++) {
            const bed = beds[bIdx];
            const bedPayload = {
              bed_number: bed.bed_number,
              label: bed.label || `Bed ${bed.bed_number}`,
              price: bed.price ? Number(bed.price) : null,
              sort_order: bIdx,
            };

            if (bed.id) {
              await ownerPropertyService.updateBed(bed.id, bedPayload);
            } else {
              await ownerPropertyService.createBed(resolvedRoomId, bedPayload);
            }
          }
        }
      }

      toast.success("Inventory structure synchronized successfully!");
      queryClient.invalidateQueries({ queryKey: ["ownedProperties"] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
      queryClient.invalidateQueries({ queryKey: ["fullProperty", propertyId] });
      queryClient.invalidateQueries({ queryKey: ["property", propertyId] });
      queryClient.invalidateQueries({ queryKey: ["propertyFloors", propertyId] });
      queryClient.invalidateQueries({ queryKey: ["floorRooms"] });
      queryClient.invalidateQueries({ queryKey: ["roomBeds"] });
      navigate("/owner/properties");
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Failed to synchronize inventory.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Image upload triggers
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!propertyId || !e.target.files) return;
    setUploadingImage(true);
    const files = Array.from(e.target.files);
    try {
      for (const file of files) {
        await ownerPropertyService.uploadPropertyImage(propertyId, file);
      }
      toast.success("Images uploaded successfully.");
      refetchImages();
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Failed to upload images.");
    } finally {
      setUploadingImage(false);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!propertyId) return;
    try {
      await ownerPropertyService.deletePropertyImage(propertyId, imageId);
      toast.success("Image deleted.");
      refetchImages();
    } catch (err) {
      toast.error("Failed to delete image.");
    }
  };

  const handleSetPrimaryImage = async (imageId: string) => {
    if (!propertyId) return;
    try {
      await ownerPropertyService.updatePropertyImage(propertyId, imageId, { is_primary: true });
      toast.success("Primary image updated.");
      refetchImages();
    } catch (err) {
      toast.error("Failed to set primary image.");
    }
  };

  const handleAltTextBlur = async (imageId: string, altText: string) => {
    if (!propertyId) return;
    try {
      await ownerPropertyService.updatePropertyImage(propertyId, imageId, { alt_text: altText });
      toast.success("Image alt text updated.");
    } catch (err) {
      toast.error("Failed to update description.");
    }
  };

  // Render correct wizard view
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-8">
            {/* Section 1: Basic Information */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <Building2 className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold text-text">Basic Information</h2>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="name" required>
                  Property Title / Name
                </Label>
                <Input
                  id="name"
                  placeholder="e.g. StaySync Premium Men's PG"
                  error={!!errors.name}
                  disabled={isSubmitting}
                  {...register("name")}
                />
                {errors.name && (
                  <p className="text-xs text-danger font-medium">
                    {errors.name.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">
                  Description
                </Label>
                <div className="relative">
                  <span className="absolute top-3 left-3 text-text-tertiary">
                    <AlignLeft className="h-4 w-4" />
                  </span>
                  <textarea
                    id="description"
                    rows={4}
                    placeholder="Provide a detailed description of the property..."
                    className="flex min-h-[100px] w-full rounded-md border border-input-border bg-input pl-10 pr-3 py-2 text-sm text-text ring-offset-bg placeholder:text-text-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isSubmitting}
                    {...register("description")}
                  />
                </div>
              </div>
            </div>

            {/* Section 2: Property & Gender Configuration */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <ClipboardList className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold text-text">Configuration</h2>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-3">
                  <Label required>Property Type</Label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { type: PropertyType.PG, label: "PG", icon: <Building2 className="h-4 w-4" /> },
                      { type: PropertyType.HOSTEL, label: "Hostel", icon: <Hotel className="h-4 w-4" /> },
                      { type: PropertyType.FLAT, label: "Flat", icon: <Home className="h-4 w-4" /> },
                      { type: PropertyType.APARTMENT, label: "Apartment", icon: <Building className="h-4 w-4" /> },
                    ].map((item) => (
                      <button
                        key={item.type}
                        type="button"
                        onClick={() => setValue("property_type", item.type)}
                        className={`flex flex-col items-center justify-center p-4 rounded-xl border text-center transition-all cursor-pointer ${
                          selectedType === item.type
                            ? "border-primary bg-primary/5 text-primary shadow-xs font-semibold ring-2 ring-primary/20"
                            : "border-border bg-bg hover:bg-bg-secondary text-text-secondary hover:text-text"
                        }`}
                        disabled={isSubmitting}
                      >
                        <div className={`mb-2 p-2 rounded-lg ${selectedType === item.type ? "bg-primary/10 text-primary" : "bg-bg-tertiary text-text-secondary"}`}>
                          {item.icon}
                        </div>
                        <span className="text-xs">{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <Label required>Gender Preference</Label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { pref: GenderPreference.COED, label: "Coed", icon: <Users className="h-4 w-4" /> },
                      { pref: GenderPreference.MALE, label: "Boys Only", icon: <User className="h-4 w-4" /> },
                      { pref: GenderPreference.FEMALE, label: "Girls Only", icon: <User className="h-4 w-4" /> },
                    ].map((item) => (
                      <button
                        key={item.pref}
                        type="button"
                        onClick={() => setValue("gender_preference", item.pref)}
                        className={`flex flex-col items-center justify-center p-4 rounded-xl border text-center transition-all cursor-pointer ${
                          selectedGender === item.pref
                            ? "border-primary bg-primary/5 text-primary shadow-xs font-semibold ring-2 ring-primary/20"
                            : "border-border bg-bg hover:bg-bg-secondary text-text-secondary hover:text-text"
                        }`}
                        disabled={isSubmitting}
                      >
                        <div className={`mb-2 p-2 rounded-lg ${selectedGender === item.pref ? "bg-primary/10 text-primary" : "bg-bg-tertiary text-text-secondary"}`}>
                          {item.icon}
                        </div>
                        <span className="text-xs">{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Section 3: Address & Location Details */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <MapPin className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold text-text">Address & Location</h2>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="address_line1" required>Address Line 1</Label>
                  <Input id="address_line1" placeholder="Plot/Street Address" error={!!errors.address_line1} disabled={isSubmitting} {...register("address_line1")} />
                  {errors.address_line1 && <p className="text-xs text-danger font-medium">{errors.address_line1.message}</p>}
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="address_line2">Address Line 2 (Optional)</Label>
                  <Input id="address_line2" placeholder="Suite/Apt/Landmark" error={!!errors.address_line2} disabled={isSubmitting} {...register("address_line2")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="city" required>City</Label>
                  <Input id="city" placeholder="City" error={!!errors.city} disabled={isSubmitting} {...register("city")} />
                  {errors.city && <p className="text-xs text-danger font-medium">{errors.city.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="state" required>State</Label>
                  <Input id="state" placeholder="State" error={!!errors.state} disabled={isSubmitting} {...register("state")} />
                  {errors.state && <p className="text-xs text-danger font-medium">{errors.state.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pincode" required>Pincode / ZIP Code</Label>
                  <Input id="pincode" placeholder="Pincode" error={!!errors.pincode} disabled={isSubmitting} {...register("pincode")} />
                  {errors.pincode && <p className="text-xs text-danger font-medium">{errors.pincode.message}</p>}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="country">Country</Label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-text-tertiary">
                      <Globe2 className="h-4 w-4" />
                    </span>
                    <Input id="country" className="pl-10" placeholder="India" error={!!errors.country} disabled={isSubmitting} {...register("country")} />
                  </div>
                </div>
              </div>
            </div>

            {/* Section 4: Coordinates Mapping */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <MapPin className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold text-text">Geolocation Mapping</h2>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="latitude">Latitude</Label>
                  <Input id="latitude" type="number" step="any" placeholder="e.g. 18.5204" disabled={isSubmitting} {...register("latitude")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="longitude">Longitude</Label>
                  <Input id="longitude" type="number" step="any" placeholder="e.g. 73.8567" disabled={isSubmitting} {...register("longitude")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="google_place_id">Google Place ID</Label>
                  <Input id="google_place_id" placeholder="Google Maps ID" disabled={isSubmitting} {...register("google_place_id")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="place_name">Google Place Name</Label>
                  <Input id="place_name" placeholder="Place Name Reference" disabled={isSubmitting} {...register("place_name")} />
                </div>
              </div>
            </div>

            {/* Section 5: Rules */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <ClipboardList className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold text-text">House Rules</h2>
              </div>
              <div className="space-y-2">
                <textarea
                  id="rules"
                  rows={4}
                  placeholder="Curfew time, visitor policy..."
                  className="flex min-h-[100px] w-full rounded-md border border-input-border bg-input px-3 py-2 text-sm text-text ring-offset-bg placeholder:text-text-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50"
                  disabled={isSubmitting}
                  {...register("rules")}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-border/50 pt-6 flex justify-between">
              <Button type="button" variant="outline" onClick={() => navigate("/owner/properties")} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="button" onClick={handleSubmit(handleSaveStep1)} loading={isSubmitting} className="font-semibold">
                {propertyId ? "Save & Continue" : "Create & Continue"}
                <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-8">
            {/* Step 2A: Amenities Checklist */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <div>
                  <h2 className="text-lg font-bold text-text">Select Amenities</h2>
                  <p className="text-xs text-text-secondary">Check-mark all services and convenience features present in your property.</p>
                </div>
              </div>

              {masterAmenities.length === 0 ? (
                <div className="flex justify-center items-center py-8">
                  <LoadingSpinner />
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {masterAmenities.map((amenity) => {
                    const isChecked = formAmenities.includes(amenity.id);
                    return (
                      <button
                        key={amenity.id}
                        type="button"
                        onClick={() => {
                          if (isChecked) {
                            setValue("amenities", formAmenities.filter((id) => id !== amenity.id));
                          } else {
                            setValue("amenities", [...formAmenities, amenity.id]);
                          }
                        }}
                        className={`flex items-center gap-2.5 p-3 rounded-lg border text-left transition-colors cursor-pointer ${
                          isChecked
                            ? "border-primary bg-primary/5 text-primary font-medium"
                            : "border-border bg-bg hover:bg-bg-secondary text-text"
                        }`}
                        disabled={isSubmitting}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}} // Controlled via button click
                          className="h-4 w-4 rounded border-border-hover text-primary focus:ring-primary/20 cursor-pointer pointer-events-none"
                          tabIndex={-1}
                        />
                        <span className="text-sm truncate capitalize">{amenity.name}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Step 2B: Image Uploads */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                <Upload className="h-5 w-5 text-primary" />
                <div>
                  <h2 className="text-lg font-bold text-text">Property Images</h2>
                  <p className="text-xs text-text-secondary">Upload high quality images of your rooms, lobby, and building catalog.</p>
                </div>
              </div>

              {/* Upload Dropzone */}
              <div className="border-2 border-dashed border-border hover:border-primary/50 transition-colors rounded-xl p-8 text-center bg-bg-secondary/20 relative">
                <input
                  type="file"
                  id="image-uploader"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleImageUpload}
                  disabled={uploadingImage || isSubmitting}
                />
                <label
                  htmlFor="image-uploader"
                  className="flex flex-col items-center justify-center cursor-pointer gap-2"
                >
                  <div className="p-3 bg-bg rounded-full border border-border shadow-xs">
                    {uploadingImage ? (
                      <LoadingSpinner />
                    ) : (
                      <Upload className="h-6 w-6 text-text-secondary" />
                    )}
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-primary hover:underline">Click to upload images</span>
                    <span className="text-text-secondary text-xs block mt-1">Accepts JPG, PNG, and WEBP. Max size 50MB per file.</span>
                  </div>
                </label>
              </div>

              {/* Uploaded Images List */}
              {propertyImages.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {propertyImages.map((image) => (
                    <Card key={image.id} className="overflow-hidden border border-border bg-card">
                      <div className="relative aspect-[4/3] bg-bg-tertiary flex items-center justify-center border-b border-border/50">
                        <img src={image.url} alt="" className="h-full w-full object-cover" />
                        
                        {image.is_primary && (
                          <div className="absolute top-2 left-2 bg-amber-500 text-white rounded-full p-1.5 shadow-md">
                            <Star className="h-4 w-4 fill-current" />
                          </div>
                        )}

                        <div className="absolute top-2 right-2 flex gap-1">
                          {!image.is_primary && (
                            <Button
                              type="button"
                              variant="secondary"
                              size="icon"
                              className="h-8 w-8 bg-black/55 text-white hover:bg-black/80 shadow-md"
                              onClick={() => handleSetPrimaryImage(image.id)}
                              title="Set as Primary"
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            className="h-8 w-8 bg-danger text-white shadow-md hover:bg-danger/90"
                            onClick={() => handleDeleteImage(image.id)}
                            disabled={isSubmitting}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <CardContent className="p-3 space-y-2">
                        <Label htmlFor={`alt-${image.id}`} className="text-xs text-text-secondary font-semibold">Image Alt Text (for accessibility)</Label>
                        <Input
                          id={`alt-${image.id}`}
                          defaultValue={image.alt_text || ""}
                          placeholder="e.g. Spacious double sharing room"
                          className="h-8 text-xs"
                          disabled={isSubmitting}
                          onBlur={(e) => handleAltTextBlur(image.id, e.target.value)}
                        />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-border/50 pt-6 flex justify-between">
              <Button type="button" variant="outline" onClick={() => changeStep(1)} disabled={isSubmitting}>
                <ArrowLeft className="mr-1.5 h-4 w-4" />
                Back to Details
              </Button>
              <Button type="button" onClick={handleSaveStep2} loading={isSubmitting} className="font-semibold">
                Save & Continue
                <ArrowRight className="ml-1.5 h-4 w-4" />
              </Button>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-8">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-primary" />
                <div>
                  <h2 className="text-lg font-bold text-text">Inventory Setup</h2>
                  <p className="text-xs text-text-secondary">Assemble the floors, room pricing, and bed availability layout.</p>
                </div>
              </div>
            </div>

            <FloorsFormSection
              control={control}
              register={register}
              getValues={getValues}
              isSubmitting={isSubmitting}
              setDeletedFloorIds={setDeletedFloorIds}
              setDeletedRoomIds={setDeletedRoomIds}
              setDeletedBedIds={setDeletedBedIds}
            />

            {/* Footer */}
            <div className="border-t border-border/50 pt-6 flex justify-between">
              <Button type="button" variant="outline" onClick={() => changeStep(2)} disabled={isSubmitting}>
                <ArrowLeft className="mr-1.5 h-4 w-4" />
                Back to Media
              </Button>
              <Button
                type="button"
                onClick={handleSubmit((data) => handleSaveStep3(data.floors))}
                loading={isSubmitting}
                className="font-semibold"
              >
                <Save className="mr-1.5 h-4 w-4" />
                Save & Finish Listing
              </Button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Wizard Steps Stepper */}
      <div className="relative flex justify-between items-center max-w-2xl mx-auto px-4">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-border -z-10" />
        
        {/* Step 1 */}
        <button
          type="button"
          onClick={() => handleStepClick(1)}
          className="flex flex-col items-center space-y-2 bg-bg px-2 z-10 cursor-pointer"
        >
          <div className={`h-10 w-10 rounded-full border-2 flex items-center justify-center font-bold text-sm shadow-sm transition-all ${
            currentStep === 1
              ? "border-primary bg-primary/10 text-primary ring-4 ring-primary/25"
              : propertyId
              ? "border-primary bg-primary text-white"
              : "border-border bg-bg-secondary text-text-tertiary"
          }`}>
            {propertyId && currentStep > 1 ? <CheckCircle2 className="h-5 w-5" /> : "1"}
          </div>
          <span className={`text-xs font-bold ${currentStep === 1 ? "text-primary" : "text-text-secondary"}`}>General Details</span>
        </button>

        {/* Step 2 */}
        <button
          type="button"
          onClick={() => handleStepClick(2)}
          className={`flex flex-col items-center space-y-2 bg-bg px-2 z-10 ${propertyId ? "cursor-pointer" : "cursor-not-allowed opacity-50"}`}
          disabled={!propertyId}
        >
          <div className={`h-10 w-10 rounded-full border-2 flex items-center justify-center font-bold text-sm shadow-sm transition-all ${
            currentStep === 2
              ? "border-primary bg-primary/10 text-primary ring-4 ring-primary/25"
              : propertyId && currentStep > 2
              ? "border-primary bg-primary text-white"
              : "border-border bg-bg-secondary text-text-tertiary"
          }`}>
            {propertyId && currentStep > 2 ? <CheckCircle2 className="h-5 w-5" /> : "2"}
          </div>
          <span className={`text-xs font-semibold ${currentStep === 2 ? "text-primary" : "text-text-secondary"}`}>Media & Amenities</span>
        </button>

        {/* Step 3 */}
        <button
          type="button"
          onClick={() => handleStepClick(3)}
          className={`flex flex-col items-center space-y-2 bg-bg px-2 z-10 ${propertyId ? "cursor-pointer" : "cursor-not-allowed opacity-50"}`}
          disabled={!propertyId}
        >
          <div className={`h-10 w-10 rounded-full border-2 flex items-center justify-center font-bold text-sm shadow-sm transition-all ${
            currentStep === 3
              ? "border-primary bg-primary/10 text-primary ring-4 ring-primary/25"
              : "border-border bg-bg-secondary text-text-tertiary"
          }`}>
            3
          </div>
          <span className={`text-xs font-semibold ${currentStep === 3 ? "text-primary" : "text-text-secondary"}`}>Inventory Setup</span>
        </button>
      </div>

      {/* Main Form Content */}
      <Card className="border-border bg-card shadow-md">
        <CardContent className="p-6 md:p-8">
          {renderStepContent()}
        </CardContent>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// STEP 3: FLOORS DYNAMIC NESTED FORM SECTIONS
// ─────────────────────────────────────────────────────────────────────────────

interface FloorsFormProps {
  control: any;
  register: any;
  getValues: any;
  isSubmitting: boolean;
  setDeletedFloorIds: React.Dispatch<React.SetStateAction<string[]>>;
  setDeletedRoomIds: React.Dispatch<React.SetStateAction<string[]>>;
  setDeletedBedIds: React.Dispatch<React.SetStateAction<string[]>>;
}

function FloorsFormSection({
  control,
  register,
  getValues,
  isSubmitting,
  setDeletedFloorIds,
  setDeletedRoomIds,
  setDeletedBedIds,
}: FloorsFormProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "floors",
  });

  const handleRemoveFloor = (index: number) => {
    // getValues() returns the raw data (without react-hook-form injected ids)
    const rawFloor = getValues(`floors.${index}`);
    if (rawFloor && rawFloor.id) {
      setDeletedFloorIds((prev) => [...prev, rawFloor.id as string]);
      // Eagerly harvest deleted children IDs
      rawFloor.rooms?.forEach((room: any) => {
        if (room.id) {
          setDeletedRoomIds((prev) => [...prev, room.id as string]);
          room.beds?.forEach((bed: any) => {
            if (bed.id) {
              setDeletedBedIds((prev) => [...prev, bed.id as string]);
            }
          });
        }
      });
    }
    remove(index);
  };

  return (
    <div className="space-y-6">
      {fields.length === 0 ? (
        <Card className="border border-dashed border-border p-8 text-center bg-bg-secondary/10">
          <CardDescription>No floors configured yet. Click the button below to add your first floor.</CardDescription>
        </Card>
      ) : (
        fields.map((field, index) => (
          <Card key={field.id} className="border border-border bg-card overflow-hidden">
            <CardHeader className="bg-bg-secondary/40 p-4 flex flex-row items-center justify-between border-b border-border/50">
              <div className="flex items-center gap-3 w-full max-w-lg">
                <div className="space-y-1">
                  <CardTitle className="text-sm font-bold text-text flex items-center gap-2">
                    Floor Configuration
                  </CardTitle>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleRemoveFloor(index)}
                className="border-danger/30 text-danger hover:bg-danger/5 hover:text-danger cursor-pointer shrink-0"
                disabled={isSubmitting}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardHeader>

            <CardContent className="p-4 md:p-6 space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor={`floors.${index}.floor_number`} required>Floor Number</Label>
                  <Input
                    id={`floors.${index}.floor_number`}
                    type="number"
                    placeholder="e.g. 0 for Ground, 1 for First"
                    error={false}
                    disabled={isSubmitting}
                    {...register(`floors.${index}.floor_number`, { required: "Floor number is required" })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`floors.${index}.name`}>Floor Label / Name (Optional)</Label>
                  <Input
                    id={`floors.${index}.name`}
                    placeholder="e.g. Ground Floor"
                    error={false}
                    disabled={isSubmitting}
                    {...register(`floors.${index}.name`)}
                  />
                </div>
              </div>

              {/* Rooms List for this floor */}
              <div className="space-y-4 pt-4 border-t border-border/40">
                <RoomsFormSection
                  control={control}
                  register={register}
                  getValues={getValues}
                  floorIndex={index}
                  isSubmitting={isSubmitting}
                  setDeletedRoomIds={setDeletedRoomIds}
                  setDeletedBedIds={setDeletedBedIds}
                />
              </div>
            </CardContent>
          </Card>
        ))
      )}

      <Button
        type="button"
        variant="outline"
        onClick={() => append({ floor_number: fields.length, name: "", description: "", sort_order: fields.length, rooms: [] })}
        disabled={isSubmitting}
        className="w-full flex items-center justify-center gap-1.5 py-5 border-dashed border-2 hover:border-primary/50 hover:bg-primary/5 transition-colors cursor-pointer"
      >
        <Plus className="h-4 w-4" />
        Add Floor Configuration
      </Button>
    </div>
  );
}

// ── Rooms Form Section ───────────────────────────────────────────────────────

interface RoomsFormProps {
  control: any;
  register: any;
  getValues: any;
  floorIndex: number;
  isSubmitting: boolean;
  setDeletedRoomIds: React.Dispatch<React.SetStateAction<string[]>>;
  setDeletedBedIds: React.Dispatch<React.SetStateAction<string[]>>;
}

function RoomsFormSection({
  control,
  register,
  getValues,
  floorIndex,
  isSubmitting,
  setDeletedRoomIds,
  setDeletedBedIds,
}: RoomsFormProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: `floors.${floorIndex}.rooms`,
  });

  const handleRemoveRoom = (index: number) => {
    // Distinguish persisted vs new: raw data will lack 'id' if newly created
    const rawRoom = getValues(`floors.${floorIndex}.rooms.${index}`);
    if (rawRoom && rawRoom.id) {
      setDeletedRoomIds((prev) => [...prev, rawRoom.id as string]);
      // Harvest child beds
      rawRoom.beds?.forEach((bed: any) => {
        if (bed.id) {
          setDeletedBedIds((prev) => [...prev, bed.id as string]);
        }
      });
    }
    remove(index);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-1">
        <h3 className="text-sm font-semibold text-text flex items-center gap-1.5">
          <Building className="h-4 w-4 text-primary" />
          Rooms Catalogue
        </h3>
      </div>

      {fields.length === 0 ? (
        <div className="p-4 rounded-lg bg-bg-secondary/40 text-center text-xs text-text-secondary border border-dashed border-border/80">
          No rooms added on this floor yet. Click below to add a room.
        </div>
      ) : (
        fields.map((field, index) => (
          <div key={field.id} className="p-4 md:p-5 rounded-xl border border-border bg-bg-secondary/20 space-y-4 relative">
            <button
              type="button"
              onClick={() => handleRemoveRoom(index)}
              className="absolute top-4 right-4 p-1.5 rounded-lg border border-border bg-card text-danger hover:bg-danger/5 hover:text-danger transition-colors cursor-pointer"
              disabled={isSubmitting}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Label required>Room Number / Name</Label>
                <Input
                  placeholder="e.g. 101"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${index}.room_number`, { required: "Room number is required" })}
                />
              </div>

              <div className="space-y-2">
                <Label required>Sharing Type</Label>
                <Controller
                  control={control}
                  name={`floors.${floorIndex}.rooms.${index}.sharing_type`}
                  rules={{ required: "Sharing type is required" }}
                  defaultValue={SharingType.DOUBLE}
                  render={({ field: controllerField }) => (
                    <select
                      className="flex h-10 w-full rounded-md border border-input-border bg-input px-3 py-2 text-sm text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={isSubmitting}
                      {...controllerField}
                    >
                      <option value={SharingType.SINGLE}>Single Sharing</option>
                      <option value={SharingType.DOUBLE}>Double Sharing</option>
                      <option value={SharingType.TRIPLE}>Triple Sharing</option>
                      <option value={SharingType.QUAD}>Quad Sharing</option>
                    </select>
                  )}
                />
              </div>

              <div className="space-y-2">
                <Label required>Price Per Bed (Monthly)</Label>
                <Input
                  type="number"
                  placeholder="e.g. 7500"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${index}.price_per_bed`, {
                    required: "Price per bed is required",
                    min: { value: 1, message: "Price must be positive" },
                  })}
                />
              </div>
            </div>

            {/* Comfort Features Checkboxes */}
            <div className="flex flex-wrap gap-x-6 gap-y-2 pt-1">
              <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-border-hover text-primary focus:ring-primary/20"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${index}.has_attached_bath`)}
                />
                Attached Bath
              </label>
              <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-border-hover text-primary focus:ring-primary/20"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${index}.has_ac`)}
                />
                Air Conditioning (AC)
              </label>
              <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-border-hover text-primary focus:ring-primary/20"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${index}.has_balcony`)}
                />
                Attached Balcony
              </label>
            </div>

            {/* Beds List for this room */}
            <div className="pt-3 border-t border-border/40">
              <BedsFormSection
                control={control}
                register={register}
                getValues={getValues}
                floorIndex={floorIndex}
                roomIndex={index}
                isSubmitting={isSubmitting}
                setDeletedBedIds={setDeletedBedIds}
              />
            </div>
          </div>
        ))
      )}

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => append({ room_number: "", name: "", sharing_type: SharingType.DOUBLE, price_per_bed: 6000, description: "", has_attached_bath: false, has_ac: false, has_balcony: false, sort_order: fields.length, beds: [] })}
        disabled={isSubmitting}
        className="flex items-center gap-1 cursor-pointer font-semibold text-xs border-primary/20 text-primary hover:bg-primary/5"
      >
        <Plus className="h-3.5 w-3.5" />
        Add Room on Floor
      </Button>
    </div>
  );
}

// ── Beds Form Section ────────────────────────────────────────────────────────

interface BedsFormProps {
  control: any;
  register: any;
  getValues: any;
  floorIndex: number;
  roomIndex: number;
  isSubmitting: boolean;
  setDeletedBedIds: React.Dispatch<React.SetStateAction<string[]>>;
}

function BedsFormSection({
  control,
  register,
  getValues,
  floorIndex,
  roomIndex,
  isSubmitting,
  setDeletedBedIds,
}: BedsFormProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: `floors.${floorIndex}.rooms.${roomIndex}.beds`,
  });

  const handleRemoveBed = (index: number) => {
    // Only add to deletion queue if it's a persisted DB bed (has a real ID in raw form values)
    const rawBed = getValues(`floors.${floorIndex}.rooms.${roomIndex}.beds.${index}`);
    if (rawBed && rawBed.id) {
      setDeletedBedIds((prev) => [...prev, rawBed.id as string]);
    }
    remove(index);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-text flex items-center gap-1">
          <Bed className="h-3.5 w-3.5 text-primary" />
          Beds Layout
        </span>
      </div>

      {fields.length === 0 ? (
        <div className="p-3 bg-bg rounded-lg text-center text-[10px] text-text-secondary border border-dashed border-border/80">
          No beds configured. Add beds to allow student holds.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
          {fields.map((field, index) => (
            <div key={field.id} className="flex gap-2 items-center p-2 rounded-lg bg-bg border border-border/60 relative pr-9">
              <div className="space-y-1 w-full">
                <Input
                  className="h-8 text-xs px-2"
                  placeholder="Bed No (e.g. A)"
                  disabled={isSubmitting}
                  {...register(`floors.${floorIndex}.rooms.${roomIndex}.beds.${index}.bed_number`, { required: true })}
                />
              </div>

              <button
                type="button"
                onClick={() => handleRemoveBed(index)}
                className="absolute right-2 text-danger hover:bg-danger/5 rounded p-1 transition-colors cursor-pointer"
                disabled={isSubmitting}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => {
          // Compute default bed number label based on index (A, B, C, D)
          const char = String.fromCharCode(65 + fields.length);
          append({ bed_number: char, label: `Bed ${char}`, price: null, sort_order: fields.length });
        }}
        disabled={isSubmitting}
        className="flex items-center gap-1 text-[11px] font-bold text-primary hover:bg-primary/5 px-2 h-7"
      >
        <Plus className="h-3 w-3" />
        Add Bed Slot
      </Button>
    </div>
  );
}
