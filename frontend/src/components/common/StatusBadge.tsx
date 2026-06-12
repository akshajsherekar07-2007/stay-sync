import { Badge } from "../ui/Badge";
import { BedStatus, PropertyStatus } from "../../types/enums";

type StatusType = BedStatus | PropertyStatus;

interface StatusBadgeProps {
  status: StatusType;
  className?: string;
}

const statusConfig: Record<StatusType, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  // BedStatus
  [BedStatus.VACANT]: { label: "Vacant", variant: "success" },
  [BedStatus.HELD]: { label: "Held", variant: "warning" },
  [BedStatus.OCCUPIED]: { label: "Occupied", variant: "destructive" },
  
  // PropertyStatus
  [PropertyStatus.DRAFT]: { label: "Draft", variant: "secondary" },
  [PropertyStatus.PENDING_REVIEW]: { label: "Pending Review", variant: "warning" },
  [PropertyStatus.ACTIVE]: { label: "Active", variant: "success" },
  [PropertyStatus.INACTIVE]: { label: "Inactive", variant: "outline" },
  [PropertyStatus.SUSPENDED]: { label: "Suspended", variant: "destructive" },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, variant: "outline" };
  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
