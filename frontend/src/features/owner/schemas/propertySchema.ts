import { z } from "zod";
import { PropertyType, GenderPreference } from "../../../types/enums";

export const propertyStep1Schema = z.object({
  name: z
    .string()
    .min(1, { message: "Property title is required" })
    .max(255, { message: "Property title must not exceed 255 characters" }),
  property_type: z.nativeEnum(PropertyType, {
    message: "Please select a valid property type",
  }),
  gender_preference: z.nativeEnum(GenderPreference, {
    message: "Please select a valid gender preference",
  }),
  address_line1: z
    .string()
    .min(1, { message: "Address is required" })
    .max(255, { message: "Address must not exceed 255 characters" }),
  address_line2: z
    .string()
    .max(255, { message: "Address Line 2 must not exceed 255 characters" })
    .nullable(),
  city: z
    .string()
    .min(1, { message: "City is required" })
    .max(100, { message: "City must not exceed 100 characters" }),
  state: z
    .string()
    .min(1, { message: "State is required" })
    .max(100, { message: "State must not exceed 100 characters" }),
  pincode: z
    .string()
    .min(1, { message: "Pincode is required" })
    .max(10, { message: "Pincode must not exceed 10 characters" }),
  country: z
    .string()
    .max(100, { message: "Country must not exceed 100 characters" }),
  latitude: z
    .union([z.number(), z.string(), z.null()]),
  longitude: z
    .union([z.number(), z.string(), z.null()]),
  google_place_id: z
    .string()
    .max(255, { message: "Google Place ID must not exceed 255 characters" })
    .nullable(),
  place_name: z
    .string()
    .max(255, { message: "Place name must not exceed 255 characters" })
    .nullable(),
  description: z
    .string()
    .max(5000, { message: "Description must not exceed 5000 characters" })
    .nullable(),
  rules: z
    .string()
    .max(5000, { message: "Rules must not exceed 5000 characters" })
    .nullable(),
});

export type PropertyStep1Input = z.infer<typeof propertyStep1Schema>;

export const bedSchema = z.object({
  id: z.string().optional(),
  bed_number: z.string().min(1, { message: "Bed number is required" }),
  label: z.string().nullable().optional(),
  price: z.union([z.number(), z.string(), z.null()]).optional(),
  sort_order: z.number().optional(),
});

export const roomSchema = z.object({
  id: z.string().optional(),
  room_number: z.string().min(1, { message: "Room number is required" }),
  name: z.string().nullable().optional(),
  sharing_type: z.string().min(1),
  price_per_bed: z.union([z.number(), z.string()]),
  description: z.string().nullable().optional(),
  has_attached_bath: z.boolean().optional(),
  has_ac: z.boolean().optional(),
  has_balcony: z.boolean().optional(),
  sort_order: z.number().optional(),
  beds: z.array(bedSchema),
});

export const floorSchema = z.object({
  id: z.string().optional(),
  floor_number: z.union([z.number(), z.string()]),
  name: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  sort_order: z.number().optional(),
  rooms: z.array(roomSchema),
});

export const propertyWizardSchema = propertyStep1Schema.extend({
  amenities: z.array(z.string()),
  floors: z.array(floorSchema),
});

export type PropertyWizardInput = z.infer<typeof propertyWizardSchema>;


