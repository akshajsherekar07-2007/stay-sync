/**
 * Status enums matching backend enum definitions.
 * See DATABASE_SCHEMA.md §2 for the authoritative list.
 */

export enum UserRole {
  STUDENT = "student",
  OWNER = "owner",
  ADMIN = "admin",
}

export enum PropertyType {
  PG = "pg",
  HOSTEL = "hostel",
  FLAT = "flat",
  APARTMENT = "apartment",
}

export enum GenderPreference {
  MALE = "male",
  FEMALE = "female",
  COED = "coed",
}

export enum SharingType {
  SINGLE = "single",
  DOUBLE = "double",
  TRIPLE = "triple",
  QUAD = "quad",
}

export enum BedStatus {
  VACANT = "vacant",
  HELD = "held",
  OCCUPIED = "occupied",
}

export enum PropertyStatus {
  DRAFT = "draft",
  PENDING_REVIEW = "pending_review",
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended",
}

/** Phase 2 enums — defined early for type completeness */
export enum HoldStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXPIRED = "expired",
  OVERRIDDEN = "overridden",
  CANCELLED = "cancelled",
}

export enum WaitlistStatus {
  ACTIVE = "active",
  PROMOTED = "promoted",
  EXPIRED = "expired",
  CANCELLED = "cancelled",
}
