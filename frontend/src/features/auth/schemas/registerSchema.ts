import { z } from "zod";
import { emailSchema, passwordSchema, fullNameSchema } from "../../../utils/validation";

export const registerSchema = z
  .object({
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string().min(1, { message: "Confirm password is required" }),
    role: z.enum(["student", "owner"], {
      message: "Role must be either student or owner",
    }),
    full_name: fullNameSchema,
    phone: z.string().optional(),
    age: z.string().optional(),
    aadhar: z.string().optional(),
    emergencyContact: z.string().optional(),
    collegeName: z.string().optional(),
    collegeYear: z.string().optional(),
    businessName: z.string().optional(),
    officeNumber: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type RegisterInput = z.infer<typeof registerSchema>;

