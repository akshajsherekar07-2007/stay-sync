/**
 * Auth-specific type definitions.
 * Matches backend schemas from app/schemas/auth.py and app/schemas/user.py.
 */

import type { UserRole } from "./enums";

// ── Request Types ────────────────────────────────────────────────────────────

/** POST /auth/register request body */
export interface RegisterRequest {
  email: string;
  password: string;
  role: UserRole.STUDENT | UserRole.OWNER;
  full_name: string;
}

/** POST /auth/login request body */
export interface LoginRequest {
  email: string;
  password: string;
}

// ── Response Types ───────────────────────────────────────────────────────────

/** Access token data returned on login/refresh */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/** Full login/register response */
export interface LoginResponse {
  token: TokenResponse;
  user_id: string;
  email: string;
  role: string;
  full_name: string | null;
}

// ── User / Profile Types ─────────────────────────────────────────────────────

/** Profile data as returned in API responses */
export interface ProfileRead {
  full_name: string;
  avatar_url: string | null;
  bio: string | null;
  college_name: string | null;
  city: string | null;
  state: string | null;
  date_of_birth: string | null;
}

/** PATCH body for updating profile (all fields optional) */
export interface ProfileUpdate {
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  college_name?: string;
  city?: string;
  state?: string;
  date_of_birth?: string;
}

/** GET /users/me response data */
export interface MeResponse {
  id: string;
  email: string;
  role: string;
  is_email_verified: boolean;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
  profile: ProfileRead | null;
}
