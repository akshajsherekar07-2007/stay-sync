import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Clock, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { holdService } from "../../../services/holdService";
import { HoldStatus } from "../../../types/hold";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function StudentHoldsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["myHolds", page, pageSize],
    queryFn: () => holdService.listMyHolds({ page, page_size: pageSize }),
  });

  const cancelMutation = useMutation({
    mutationFn: (holdId: string) => holdService.cancelHold(holdId),
    onSuccess: () => {
      toast.success("Hold cancelled successfully.");
      queryClient.invalidateQueries({ queryKey: ["myHolds"] });
      queryClient.invalidateQueries({ queryKey: ["studentDashboardData"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to cancel hold.");
    },
  });

  const holds = data?.data || [];
  const pagination = data?.pagination;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/dashboard">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <h1 className="text-2xl font-bold text-text">My Bed Holds</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : holds.length === 0 ? (
        <Card className="bg-bg border-border text-center py-12 shadow-xs">
          <CardContent>
            <Clock className="h-12 w-12 text-text-tertiary mx-auto mb-4" />
            <h3 className="text-lg font-bold text-text">No Holds Found</h3>
            <p className="text-text-secondary mt-2">You haven't requested any bed holds yet.</p>
            <Button className="mt-6" asChild>
              <Link to="/properties">Browse Properties</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {holds.map((hold) => (
            <Card key={hold.id} className="bg-card border-border shadow-xs overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border-b border-border/50 bg-bg-secondary/20">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-text">Hold Request</span>
                    <Badge
                      variant={
                        hold.status === HoldStatus.APPROVED ? "success" :
                        hold.status === HoldStatus.PENDING ? "warning" :
                        hold.status === HoldStatus.REJECTED ? "destructive" :
                        hold.status === HoldStatus.CANCELLED ? "outline" : "secondary"
                      }
                      className="capitalize"
                    >
                      {hold.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-text-secondary">
                    Requested on {new Date(hold.requested_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="mt-3 sm:mt-0 text-right">
                  {hold.status === HoldStatus.PENDING && (
                    <Button
                      variant="destructive"
                      size="sm"
                      className="w-full sm:w-auto"
                      disabled={cancelMutation.isPending}
                      onClick={() => cancelMutation.mutate(hold.id)}
                    >
                      Cancel Request
                    </Button>
                  )}
                  {hold.status === HoldStatus.APPROVED && hold.expires_at && (
                    <div className="text-xs">
                      <span className="text-text-secondary">Expires: </span>
                      <span className="font-bold text-amber-600">
                        {new Date(hold.expires_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <CardContent className="p-5">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="block text-text-secondary text-xs">Duration</span>
                    <span className="font-semibold text-text">{hold.hold_duration_hours} hours</span>
                  </div>
                  {hold.resolution_note && (
                    <div className="col-span-2">
                      <span className="block text-text-secondary text-xs">Owner Note</span>
                      <span className="font-medium text-text bg-bg-secondary p-2 rounded block mt-1">
                        {hold.resolution_note}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          
          {pagination && pagination.total_pages > 1 && (
            <div className="flex justify-between items-center mt-6">
              <Button
                variant="outline"
                disabled={!pagination.has_prev}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-text-secondary">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <Button
                variant="outline"
                disabled={!pagination.has_next}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
