import { Badge } from "../../../components/ui/Badge";
import type { RoomRead } from "../../../types/property";

interface RoomCardProps {
  room: RoomRead;
  isSelected: boolean;
  onClick: () => void;
}

export function RoomCard({ room, isSelected, onClick }: RoomCardProps) {
  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-2xl border border-transparent text-left transition-all duration-200 flex flex-col justify-between cursor-pointer w-full group relative overflow-hidden ${
        isSelected
          ? "bg-primary/10 shadow-md ring-2 ring-primary/40"
          : "bg-card shadow-sm hover:shadow-lg hover:ring-1 hover:ring-primary/30 hover:bg-bg-secondary"
      }`}
    >
      {/* Decorative gradient blob on hover for non-selected state */}
      {!isSelected && (
        <div className="absolute -right-4 -top-4 w-16 h-16 bg-primary/5 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      )}

      <div className="relative z-10 w-full">
        <div className="flex justify-between items-start mb-2">
          <span className="text-base font-extrabold text-text tracking-tight">Room {room.room_number}</span>
          <Badge variant={isSelected ? "default" : "outline"} className={`text-[10px] uppercase tracking-wider py-0.5 px-2 ${isSelected ? 'shadow-sm' : ''}`}>
            {room.sharing_type} Share
          </Badge>
        </div>
        <p className="text-xs text-text-secondary line-clamp-1 font-medium">
          {room.name || "Standard Student Room"}
        </p>
      </div>

      <div className="flex justify-between items-end mt-5 pt-3 border-t border-border/20 w-full text-sm relative z-10">
        <span className="text-[11px] text-text-secondary font-medium">Rent / Bed</span>
        <span className={`font-bold ${isSelected ? 'text-primary' : 'text-text group-hover:text-primary transition-colors'}`}>
          ₹{room.price_per_bed.toLocaleString("en-IN")}
        </span>
      </div>
    </button>
  );
}
