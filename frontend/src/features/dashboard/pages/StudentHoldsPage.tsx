import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Clock, ArrowLeft, XCircle } from "lucide-react";
import { toast } from "sonner";

import { holdService } from "../../../services/holdService";
import { HoldStatus } from "../../../types/hold";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import { EmptyState } from "../../../components/common/EmptyState";

export default function StudentHoldsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [clearedHolds, setClearedHolds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("student_cleared_holds");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const handleClear = (holdId: string) => {
    const newCleared = [...clearedHolds, holdId];
    setClearedHolds(newCleared);
    localStorage.setItem("student_cleared_holds", JSON.stringify(newCleared));
  };

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

  const rawHolds = data?.data || [];
  const pagination = data?.pagination;

  const visibleHolds = rawHolds.filter(hold => {
    // Hide rejected holds that the student has cleared
    if (clearedHolds.includes(hold.id)) return false;

    // Hide approved holds that have passed their 24h expiration
    if (hold.status === HoldStatus.APPROVED && hold.expires_at) {
      if (new Date(hold.expires_at).getTime() < Date.now()) {
        return false;
      }
    }

    return true;
  });

  return (
    <div className="w-full mx-auto space-y-6 pb-8">
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
      ) : visibleHolds.length === 0 ? (
        <EmptyState
          icon={<Clock className="h-10 w-10 text-primary" />}
          title="No Holds Found"
          description="You haven't requested any bed holds yet or they have all expired/been cleared."
          action={
            <Button asChild>
              <Link to="/properties">Browse Properties</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-4">
          {visibleHolds.map((hold) => (
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
                <div className="mt-3 sm:mt-0 flex gap-2 justify-end">
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
                  {(hold.status === HoldStatus.REJECTED || hold.status === HoldStatus.CANCELLED) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleClear(hold.id)}
                      className="flex items-center gap-1.5 text-text-secondary hover:text-text bg-bg hover:bg-bg-secondary"
                    >
                      <XCircle className="h-4 w-4" /> Clear
                    </Button>
                  )}
                  {hold.status === HoldStatus.APPROVED && hold.expires_at && (
                    <div className="text-xs text-right">
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
                      <span className="block text-text-secondary text-xs flex items-center gap-2">Owner Note</span>
                      <span className="font-medium text-text bg-bg-secondary/50 border border-border/50 px-3 py-2 rounded-lg inline-block mt-1">
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
