
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
}

export function WaitlistCard({ entry }: WaitlistCardProps) {
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
    <Card className="border-border bg-card overflow-hidden transition-all hover:border-border-hover">
      <CardContent className="p-0">
        <div className="flex flex-col sm:flex-row border-b border-border/50">
          {/* Status & Position Column */}
          <div className="bg-bg-secondary/40 p-4 sm:w-1/3 flex flex-col items-center justify-center border-b sm:border-b-0 sm:border-r border-border/50">
            <div className="text-center">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider block mb-1">Queue Position</span>
              {entry.status === WaitlistStatus.ACTIVE ? (
                <div className="text-4xl font-extrabold text-primary flex items-center justify-center gap-1">
                  <span className="text-xl text-primary/50">#</span>{entry.position}
                </div>
              ) : (
                <div className="text-2xl font-bold text-text-secondary">—</div>
              )}
            </div>
            <div className="mt-3">
              {getStatusBadge(entry.status)}
            </div>
          </div>

          {/* Property Info Column */}
          <div className="p-4 sm:w-2/3 flex flex-col justify-between space-y-4">
            <div>
              {isPropertyLoading ? (
                <div className="animate-pulse space-y-2">
                  <div className="h-5 bg-bg-tertiary rounded w-3/4"></div>
                  <div className="h-4 bg-bg-tertiary rounded w-1/2"></div>
                </div>
              ) : property ? (
                <>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-text text-base line-clamp-1 flex items-center gap-1.5">
                        <Building2 className="h-4 w-4 text-text-secondary shrink-0" />
                        {property.name}
                      </h3>
                      <p className="text-xs text-text-secondary mt-1 flex items-center gap-1">
                        <MapPin className="h-3 w-3 shrink-0" />
                        {property.city}, {property.state}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-sm text-text-secondary">Property information unavailable</div>
              )}

              <div className="mt-4 pt-3 border-t border-border/40 grid grid-cols-2 gap-2">
                <div>
                  <span className="block text-[10px] text-text-tertiary uppercase">Joined On</span>
                  <span className="text-xs text-text flex items-center gap-1">
                    <Clock className="h-3 w-3 text-text-secondary" />
                    {new Date(entry.joined_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="block text-[10px] text-text-tertiary uppercase">Bed ID</span>
                  <span className="text-xs text-text font-mono" title={entry.bed_id}>
                    {entry.bed_id.split('-')[0]}...
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            {entry.status === WaitlistStatus.ACTIVE && (
              <div className="flex justify-end pt-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-danger border-danger/20 hover:bg-danger/10 hover:text-danger h-8 text-xs"
                  onClick={() => cancelMutation.mutate()}
                  disabled={cancelMutation.isPending}
                >
                  <XCircle className="h-3.5 w-3.5 mr-1" />
                  {cancelMutation.isPending ? "Cancelling..." : "Leave Waitlist"}
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
