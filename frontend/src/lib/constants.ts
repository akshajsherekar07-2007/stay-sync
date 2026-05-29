/**
 * Application-wide constants.
 * Matches backend constants defined in app/core/constants.py.
 */

export const APP_NAME = "StaySync";

/** Bed status constants (maps to backend BedStatus enum) */
export const BED_STATUS = {
  VACANT: "vacant",
  HELD: "held",
  OCCUPIED: "occupied",
} as const;

/** Bed status display colors */
export const BED_STATUS_COLORS = {
  [BED_STATUS.VACANT]: "#22c55e",   // 🟢 Green
  [BED_STATUS.HELD]: "#eab308",     // 🟡 Yellow
  [BED_STATUS.OCCUPIED]: "#ef4444", // 🔴 Red
} as const;

/** User roles */
export const USER_ROLES = {
  STUDENT: "student",
  OWNER: "owner",
  ADMIN: "admin",
} as const;

/** Pagination defaults */
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;
