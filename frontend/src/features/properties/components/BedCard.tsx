import { Bed } from "lucide-react";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import type { BedRead } from "../../../types/property";
import styles from "./BedCard.module.css";

export interface HoldData {
  id: string;
  bed_id: string;
  status: string;
}

interface BedCardProps {
  bed: BedRead;
  myActiveHold?: HoldData;
  onHoldRequest: (bedId: string) => void;
  isHolding?: boolean;
}

export function BedCard({ bed, myActiveHold, onHoldRequest, isHolding = false }: BedCardProps) {
  const isVacant = bed.status === "vacant";
  const isHeld = bed.status === "held";

  // Base styling depending on status
  const getStatusStyles = () => {
    if (isVacant) return styles.cardVacant;
    if (isHeld) return styles.cardHeld;
    return styles.cardOccupied;
  };

  const getIconStyles = () => {
    if (isVacant) return styles.iconVacant;
    if (isHeld) return styles.iconHeld;
    return styles.iconOccupied;
  };

  return (
    <div
      className={`${styles.card} ${getStatusStyles()}`}
    >
      <div className={styles.leftContent}>
        <div className={`${styles.iconWrapper} ${getIconStyles()}`}>
          <Bed className={styles.bedIcon} />
        </div>
        <div className={styles.bedInfo}>
          <span className={styles.bedNumber}>Bed {bed.bed_number}</span>
          <span className={styles.bedLabel}>
            {bed.label || "Regular Bed"}
          </span>
        </div>
      </div>

      <div className={styles.rightContent}>
        <span className={styles.price}>
          {bed.price ? `₹${bed.price.toLocaleString("en-IN")}` : "Included"}
        </span>
        
        {myActiveHold ? (
          <Badge variant="success" className={styles.holdBadge}>
            Your Hold
          </Badge>
        ) : isVacant ? (
          <Button
            size="sm"
            variant="outline"
            disabled={isHolding}
            className={styles.holdBtn}
            onClick={() => onHoldRequest(bed.id)}
          >
            {isHolding ? "Holding..." : "Hold Bed"}
          </Button>
        ) : (
          <Badge
            variant={isHeld ? "warning" : "destructive"}
            className={styles.statusBadge}
          >
            {bed.status}
          </Badge>
        )}
      </div>
    </div>
  );
}
