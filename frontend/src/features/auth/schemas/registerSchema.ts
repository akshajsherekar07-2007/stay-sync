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
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type RegisterInput = z.infer<typeof registerSchema>;

