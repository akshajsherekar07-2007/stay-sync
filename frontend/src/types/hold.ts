export enum HoldStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXPIRED = "expired",
  OVERRIDDEN = "overridden",
  CANCELLED = "cancelled",
}

export interface HoldRequestCreate {
  bed_id: string;
  hold_duration_hours?: number;
}

export interface HoldRequestUpdate {
  status?: HoldStatus;
  resolution_note?: string;
}

export interface HoldRequestRead {
  id: string;
  bed_id: string;
  student_id: string;
  property_id: string;
  status: HoldStatus;
  hold_duration_hours: number;
  requested_at: string;
  approved_at: string | null;
  expires_at: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface HoldRequestWithDetails extends HoldRequestRead {
  // Can be extended later if the backend starts embedding relation data
  // like property_name, room_number, bed_number. For now, it mirrors Read.
}
