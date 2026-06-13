import type { PropertyType, GenderPreference, PropertyStatus } from "./enums";
import type { Property } from "./models";

export interface PropertyCreate {
  name: string;
  description?: string | null;
  property_type: PropertyType | string;
  gender_preference?: GenderPreference | string;
  address_line1: string;
  address_line2?: string | null;
  city: string;
  state: string;
  pincode: string;
  country?: string;
  latitude?: number | null;
  longitude?: number | null;
  google_place_id?: string | null;
  place_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  rules?: string | null;
}

export interface PropertyUpdate {
  name?: string;
  description?: string | null;
  property_type?: PropertyType | string;
  gender_preference?: GenderPreference | string;
  address_line1?: string;
  address_line2?: string | null;
  city?: string;
  state?: string;
  pincode?: string;
  country?: string;
  latitude?: number | null;
  longitude?: number | null;
  google_place_id?: string | null;
  place_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  rules?: string | null;
}

export interface PropertyStatusUpdate {
  status: PropertyStatus | string;
}

export interface PropertyRead extends Property {
  address_line2: string | null;
  country: string;
  google_place_id: string | null;
  place_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  last_refreshed_at: string | null;
  rules: string | null;
}

export interface PropertyListItem {
  id: string;
  owner_id: string;
  name: string;
  property_type: PropertyType | string;
  gender_preference: GenderPreference | string;
  city: string;
  state: string;
  pincode: string;
  min_price: number | null;
  max_price: number | null;
  total_beds: number;
  available_beds: number;
  status: PropertyStatus | string;
  is_verified: boolean;
  created_at: string;
  primary_image_url: string | null;
  is_saved: boolean;
}

export interface ImageRead {
  id: string;
  entity_type: string;
  entity_id: string;
  property_id: string;
  url: string;
  alt_text: string | null;
  sort_order: number;
  is_primary: boolean;
  file_size_bytes: number | null;
  mime_type: string | null;
  created_at: string;
}

export interface ImageUpdate {
  alt_text?: string | null;
  is_primary?: boolean;
}

export interface ImageReorderItem {
  id: string;
  sort_order: number;
}

export interface ImageReorder {
  images: ImageReorderItem[];
}

export interface AmenityAttach {
  amenity_ids: string[];
}

export interface AmenityRead {
  id: string;
  name: string;
  icon: string | null;
  category: string | null;
}

export interface FloorRead {
  id: string;
  property_id: string;
  floor_number: number;
  name: string | null;
  description: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface RoomRead {
  id: string;
  floor_id: string;
  property_id: string;
  room_number: string;
  name: string | null;
  sharing_type: string;
  price_per_bed: number;
  description: string | null;
  has_attached_bath: boolean;
  has_ac: boolean;
  has_balcony: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface BedRead {
  id: string;
  room_id: string;
  property_id: string;
  bed_number: string;
  label: string | null;
  status: string;
  price: number | null;
  version: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

