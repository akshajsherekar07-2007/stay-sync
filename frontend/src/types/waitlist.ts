import type { WaitlistStatus } from "./enums";

export interface WaitlistEntryRead {
  id: string;
  bed_id: string;
  student_id: string;
  property_id: string;
  position: number;
  status: WaitlistStatus;
  joined_at: string;
  promoted_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaitlistEntryCreate {
  bed_id: string;
}

export interface WaitlistPositionResponse {
  position: number;
}
