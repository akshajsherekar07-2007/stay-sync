import { z } from "zod";

/**
 * Shared validation schemas matching backend Pydantic validation rules.
 */

export const emailSchema = z
  .string()
  .min(1, { message: "Email is required" })
  .email({ message: "Invalid email address" });

export const passwordSchema = z
  .string()
  .min(8, { message: "Password must be at least 8 characters" })
  .max(128, { message: "Password must not exceed 128 characters" })
  .refine((val) => /[A-Z]/.test(val), {
    message: "Password must contain at least one uppercase letter",
  })
  .refine((val) => /\d/.test(val), {
    message: "Password must contain at least one digit",
  });

export const fullNameSchema = z
  .string()
  .min(2, { message: "Full name must be at least 2 characters" })
  .max(150, { message: "Full name must not exceed 150 characters" })
  .transform((val) => val.trim());
