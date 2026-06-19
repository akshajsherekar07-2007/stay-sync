
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock, Building2, MapPin, XCircle } from "lucide-react";

import type { WaitlistEntryRead } from "../../../types/waitlist";
import { WaitlistStatus } from "../../../types/enums";
import { propertyService } from "../../../services/propertyService";
import { waitlistService } from "../../../services/waitlistService";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";

interface WaitlistCardProps {
  entry: WaitlistEntryRead;
  onClear?: () => void;
}

export function WaitlistCard({ entry, onClear }: WaitlistCardProps) {
  const queryClient = useQueryClient();

  // Fetch property details for this waitlist entry
  const { data: propertyResponse, isLoading: isPropertyLoading } = useQuery({
    queryKey: ["property", entry.property_id],
    queryFn: () => propertyService.getProperty(entry.property_id),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const property = propertyResponse?.data;

  // Cancel waitlist mutation
  const cancelMutation = useMutation({
    mutationFn: () => waitlistService.cancelWaitlist(entry.id),
    onSuccess: () => {
      // Invalidate the waitlist query to refresh the list
      queryClient.invalidateQueries({ queryKey: ["myWaitlists"] });
    },
    onError: (error) => {
      console.error("Failed to cancel waitlist:", error);
      // In a real app, we'd show a toast notification here
    },
  });

  const getStatusBadge = (status: WaitlistStatus) => {
    switch (status) {
      case WaitlistStatus.ACTIVE:
        return <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/20">Active</Badge>;
      case WaitlistStatus.PROMOTED:
        return <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">Promoted</Badge>;
      case WaitlistStatus.EXPIRED:
        return <Badge variant="outline" className="bg-gray-500/10 text-gray-600 border-gray-500/20">Expired</Badge>;
      case WaitlistStatus.CANCELLED:
        return <Badge variant="outline" className="bg-danger/10 text-danger border-danger/20">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white rounded-xl border border-border/60 shadow-sm hover:border-primary/30 transition-all hover:shadow-md">
      <div className="flex items-center gap-4 flex-1">
        {/* Status / Position Block */}
        <div className="shrink-0 bg-bg-secondary rounded-lg p-3 flex flex-col items-center justify-center min-w-[80px] border border-border/40">
          <span className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider mb-1">Queue</span>
          {entry.status === WaitlistStatus.ACTIVE ? (
            <div className="text-xl font-black text-primary flex items-center justify-center">
              <span className="text-sm text-primary/50 mr-0.5">#</span>{entry.position}
            </div>
          ) : (
            <div className="text-xl font-bold text-text-secondary">—</div>
          )}
        </div>
        
        {/* Details Block */}
        <div className="flex flex-col justify-center flex-1 min-w-0">
          {isPropertyLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-bg-tertiary rounded w-1/2"></div>
              <div className="h-3 bg-bg-tertiary rounded w-1/3"></div>
            </div>
          ) : property ? (
            <div>
              <h3 className="font-bold text-text text-base truncate flex items-center gap-1.5">
                <Building2 className="h-4 w-4 text-text-secondary shrink-0" />
                {property.name}
              </h3>
              <p className="text-xs text-text-secondary mt-1 flex items-center gap-1 truncate">
                <MapPin className="h-3 w-3 shrink-0" />
                {property.city}, {property.state}
              </p>
            </div>
          ) : (
            <div className="text-sm text-text-secondary">Property information unavailable</div>
          )}

          <div className="flex items-center gap-3 mt-3">
             {getStatusBadge(entry.status)}
             <span className="text-[11px] font-medium text-text-secondary flex items-center gap-1">
               <Clock className="h-3 w-3" />
               {new Date(entry.joined_at).toLocaleDateString()}
             </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center sm:justify-end shrink-0 gap-2">
        {entry.status === WaitlistStatus.ACTIVE && (
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-danger hover:bg-danger/10 hover:text-danger h-8 text-xs font-semibold rounded-lg sm:opacity-0 sm:group-hover:opacity-100 transition-opacity w-full sm:w-auto border border-danger/10 sm:border-none"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
          >
            <XCircle className="h-3.5 w-3.5 mr-1" />
            {cancelMutation.isPending ? "Cancelling..." : "Leave"}
          </Button>
        )}
        {entry.status === WaitlistStatus.CANCELLED && onClear && (
          <Button 
            variant="outline" 
            size="sm" 
            onClick={onClear}
            className="flex items-center gap-1.5 text-text-secondary hover:text-text bg-bg hover:bg-bg-secondary w-full sm:w-auto"
          >
            <XCircle className="h-4 w-4" /> Clear
          </Button>
        )}
      </div>
    </div>
  );
}
