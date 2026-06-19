import { Bed } from "lucide-react";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import type { BedRead } from "../../../types/property";

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
    if (isVacant) return "border-transparent hover:bg-emerald-500/5 hover:shadow-md ring-1 ring-emerald-500/20";
    if (isHeld) return "border-transparent bg-amber-500/5 ring-1 ring-amber-500/20";
    return "border-transparent bg-rose-500/5 opacity-75 grayscale-[0.2] ring-1 ring-rose-500/10";
  };

  const getIconStyles = () => {
    if (isVacant) return "bg-emerald-500/15 text-emerald-600 shadow-inner";
    if (isHeld) return "bg-amber-500/15 text-amber-600";
    return "bg-rose-500/15 text-rose-600";
  };

  return (
    <div
      className={`flex items-center justify-between p-5 rounded-2xl border bg-card transition-all duration-300 ${getStatusStyles()}`}
    >
      <div className="flex items-center gap-4">
        <div className={`h-12 w-12 flex items-center justify-center rounded-xl ${getIconStyles()}`}>
          <Bed className="h-6 w-6" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-extrabold text-text tracking-tight">Bed {bed.bed_number}</span>
          <span className="text-[11px] text-text-secondary font-medium">
            {bed.label || "Regular Bed"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm font-bold text-text">
          {bed.price ? `₹${bed.price.toLocaleString("en-IN")}` : "Included"}
        </span>
        
        {myActiveHold ? (
          <Badge variant="success" className="text-[11px] py-1 px-3 shadow-sm bg-emerald-500 hover:bg-emerald-600 border-none font-semibold">
            Your Hold
          </Badge>
        ) : isVacant ? (
          <Button
            size="sm"
            variant="outline"
            disabled={isHolding}
            className="text-[11px] py-1 h-8 px-4 font-bold cursor-pointer border-emerald-500/50 text-emerald-600 hover:bg-emerald-500 hover:text-white transition-all shadow-sm active:scale-95"
            onClick={() => onHoldRequest(bed.id)}
          >
            {isHolding ? "Holding..." : "Hold Bed"}
          </Button>
        ) : (
          <Badge
            variant={isHeld ? "warning" : "destructive"}
            className="text-[10px] py-1 px-3 uppercase tracking-wider text-white shadow-sm border-none font-semibold"
          >
            {bed.status}
          </Badge>
        )}
      </div>
    </div>
  );
}
