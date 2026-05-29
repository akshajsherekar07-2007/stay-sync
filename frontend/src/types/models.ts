/**
 * Domain model type definitions.
 * These represent the shape of data returned from the API.
 * Models will be expanded as features are implemented.
 */

import type { PropertyType, GenderPreference, PropertyStatus, BedStatus, SharingType } from "./enums";

/** Base fields present on all entities */
export interface BaseModel {
  id: string;
  created_at: string;
  updated_at: string;
}

/** User (public-safe subset) */
export interface User extends BaseModel {
  email: string;
  role: string;
  is_email_verified: boolean;
  is_active: boolean;
}

/** User profile */
export interface Profile extends BaseModel {
  user_id: string;
  full_name: string;
  avatar_url: string | null;
  bio: string | null;
  college_name: string | null;
  city: string | null;
  state: string | null;
}

/** Property listing */
export interface Property extends BaseModel {
  owner_id: string;
  name: string;
  description: string | null;
  property_type: PropertyType;
  gender_preference: GenderPreference;
  address_line1: string;
  city: string;
  state: string;
  pincode: string;
  latitude: number | null;
  longitude: number | null;
  min_price: number | null;
  max_price: number | null;
  total_beds: number;
  available_beds: number;
  status: PropertyStatus;
  is_verified: boolean;
}

/** Bed (atomic inventory unit) */
export interface Bed extends BaseModel {
  room_id: string;
  property_id: string;
  bed_number: string;
  label: string | null;
  status: BedStatus;
  price: number | null;
}

/** Room */
export interface Room extends BaseModel {
  floor_id: string;
  property_id: string;
  room_number: string;
  sharing_type: SharingType;
  price_per_bed: number;
  beds: Bed[];
}

/** Floor */
export interface Floor extends BaseModel {
  property_id: string;
  floor_number: number;
  name: string | null;
  rooms: Room[];
}

/** Amenity */
export interface Amenity {
  id: string;
  name: string;
  icon: string | null;
  category: string | null;
}
