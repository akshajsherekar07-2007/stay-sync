import { Badge } from "../../../components/ui/Badge";
import type { RoomRead } from "../../../types/property";
import styles from "./RoomCard.module.css";

interface RoomCardProps {
  room: RoomRead;
  isSelected: boolean;
  onClick: () => void;
}

export function RoomCard({ room, isSelected, onClick }: RoomCardProps) {
  return (
    <button
      onClick={onClick}
      className={`${styles.card} ${isSelected ? styles.cardSelected : ""}`}
    >
      {/* Decorative gradient blob on hover for non-selected state */}
      {!isSelected && (
        <div className={styles.hoverBlob} />
      )}

      <div className={styles.contentWrapper}>
        <div className={styles.headerRow}>
          <span className={styles.roomTitle}>Room {room.room_number}</span>
          <Badge variant={isSelected ? "default" : "outline"} className={`${styles.badgeBase} ${isSelected ? styles.badgeSelected : ''}`}>
            {room.sharing_type} Share
          </Badge>
        </div>
        <p className={styles.roomDesc}>
          {room.name || "Standard Student Room"}
        </p>
      </div>

      <div className={styles.footerRow}>
        <span className={styles.priceLabel}>Rent / Bed</span>
        <span className={isSelected ? styles.priceValueSelected : styles.priceValue}>
          ₹{room.price_per_bed.toLocaleString("en-IN")}
        </span>
      </div>
    </button>
  );
}
