export enum NotificationType {
  SYSTEM = "system",
  MAINTENANCE = "maintenance",
  HOLD_APPROVED = "hold_approved",
  HOLD_REJECTED = "hold_rejected",
  HOLD_EXPIRED = "hold_expired",
  WAITLIST_PROMOTED = "waitlist_promoted",
  PAYMENT_REMINDER = "payment_reminder",
  PAYMENT_RECEIVED = "payment_received",
}

export interface NotificationRead {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data: Record<string, any> | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}
