import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { CheckCircle2, XCircle, Clock, ArrowLeft, Building2 } from "lucide-react";
import { toast } from "sonner";

import { holdService } from "../../../services/holdService";
import { ownerPropertyService } from "../../../services/ownerPropertyService";
import { HoldStatus } from "../../../types/hold";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function OwnerHoldsPage() {
  const queryClient = useQueryClient();
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // 1. Fetch owner's properties to select from
  const { data: propertiesData, isLoading: isPropertiesLoading } = useQuery({
    queryKey: ["ownerProperties"],
    queryFn: () => ownerPropertyService.listOwnedProperties(),
  });

  const properties = propertiesData?.data || [];

  // Auto-select first property if none selected
  useEffect(() => {
    if (properties.length > 0 && !selectedPropertyId) {
      setSelectedPropertyId(properties[0].id);
    }
  }, [properties, selectedPropertyId]);

  // 2. Fetch holds for the selected property
  const { data: holdsData, isLoading: isHoldsLoading } = useQuery({
    queryKey: ["propertyHolds", selectedPropertyId, page, pageSize],
    queryFn: () => holdService.listPropertyHolds(selectedPropertyId!, { page, page_size: pageSize }),
    enabled: !!selectedPropertyId,
  });

  const approveMutation = useMutation({
    mutationFn: (holdId: string) => holdService.approveHold(holdId),
    onSuccess: () => {
      toast.success("Hold approved successfully.");
      queryClient.invalidateQueries({ queryKey: ["propertyHolds", selectedPropertyId] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to approve hold.");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ holdId, reason }: { holdId: string; reason: string }) => 
      holdService.rejectHold(holdId, { status: HoldStatus.REJECTED, resolution_note: reason }),
    onSuccess: () => {
      toast.success("Hold rejected.");
      queryClient.invalidateQueries({ queryKey: ["propertyHolds", selectedPropertyId] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || "Failed to reject hold.");
    },
  });

  const holds = holdsData?.data || [];
  const pagination = holdsData?.pagination;

  const [clearedHolds, setClearedHolds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("owner_cleared_holds");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const handleClear = (holdId: string) => {
    const newCleared = [...clearedHolds, holdId];
    setClearedHolds(newCleared);
    localStorage.setItem("owner_cleared_holds", JSON.stringify(newCleared));
  };

  const handleReject = (holdId: string) => {
    const reason = prompt("Please enter a reason for rejection:");
    if (reason !== null) {
      rejectMutation.mutate({ holdId, reason });
    }
  };

  const now = new Date();
  const visibleHolds = holds.filter((hold) => {
    // Hide rejected holds that the owner has cleared
    if (clearedHolds.includes(hold.id)) return false;
    
    // Hide approved holds if they have expired
    if (hold.status === HoldStatus.APPROVED && hold.expires_at) {
      if (new Date(hold.expires_at) < now) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-10 w-full mx-auto pb-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden mb-4 flex flex-col sm:flex-row sm:items-start justify-between gap-6">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text mb-2">
            Hold Approvals
          </h1>
          <p className="text-sm text-text-secondary">
            Review and manage pending bed hold requests from students.
          </p>
        </div>

        {!isPropertiesLoading && properties.length > 0 && (
          <div className="flex items-center gap-3 bg-white px-4 py-2.5 rounded-xl border border-border/60 shadow-sm shrink-0">
            <span className="text-sm font-semibold text-text-secondary">Property:</span>
            <select
              className="bg-transparent text-sm font-bold text-text focus:outline-none cursor-pointer pr-4"
              value={selectedPropertyId || ""}
              onChange={(e) => {
                setSelectedPropertyId(e.target.value);
                setPage(1);
              }}
            >
              {properties.map((prop) => (
                <option key={prop.id} value={prop.id}>
                  {prop.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {isPropertiesLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : properties.length === 0 ? (
        <Card className="bg-bg border-border text-center py-12 shadow-xs">
          <CardContent>
            <Building2 className="h-12 w-12 text-text-tertiary mx-auto mb-4" />
            <h3 className="text-lg font-bold text-text">No Properties Found</h3>
            <p className="text-text-secondary mt-2">You need to list a property before managing holds.</p>
            <Button className="mt-6" asChild>
              <Link to="/owner/properties/create">Create Property</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {isHoldsLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : visibleHolds.length === 0 ? (
            <Card className="bg-bg border-border text-center py-12 shadow-xs">
              <CardContent>
                <Clock className="h-12 w-12 text-text-tertiary mx-auto mb-4" />
                <h3 className="text-lg font-bold text-text">No Holds Found</h3>
                <p className="text-text-secondary mt-2">There are no hold requests for this property.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
              <div className="divide-y divide-border/40">
                {visibleHolds.map((hold) => (
                  <div key={hold.id} className="p-4 sm:p-6 hover:bg-bg-secondary/30 transition-colors">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-text">Hold #{hold.id.slice(0, 8)}</span>
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

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {hold.status === HoldStatus.PENDING && (
                          <>
                            <Button
                              variant="destructive"
                              size="sm"
                              disabled={rejectMutation.isPending || approveMutation.isPending}
                              onClick={() => handleReject(hold.id)}
                              className="flex items-center gap-1.5"
                            >
                              <XCircle className="h-4 w-4" /> Reject
                            </Button>
                            <Button
                              variant="default"
                              size="sm"
                              disabled={approveMutation.isPending || rejectMutation.isPending}
                              onClick={() => approveMutation.mutate(hold.id)}
                              className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
                            >
                              <CheckCircle2 className="h-4 w-4" /> Approve
                            </Button>
                          </>
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
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm bg-bg-secondary/30 p-4 rounded-xl border border-border/30">
                      <div>
                        <span className="block text-text-secondary text-xs mb-0.5">Student ID</span>
                        <span className="font-semibold text-text text-xs font-mono">{hold.student_id.slice(0, 8)}...</span>
                      </div>
                      <div>
                        <span className="block text-text-secondary text-xs mb-0.5">Bed ID</span>
                        <span className="font-semibold text-text text-xs font-mono">{hold.bed_id.slice(0, 8)}...</span>
                      </div>
                      <div>
                        <span className="block text-text-secondary text-xs mb-0.5">Duration</span>
                        <span className="font-semibold text-text">{hold.hold_duration_hours} hours</span>
                      </div>
                      {hold.expires_at && (
                        <div>
                          <span className="block text-text-secondary text-xs mb-0.5">Expires At</span>
                          <span className="font-bold text-amber-600">
                            {new Date(hold.expires_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {hold.resolution_note && (
                        <div className="col-span-2 md:col-span-4 mt-2">
                          <span className="block text-text-secondary text-xs mb-1">Resolution Note</span>
                          <span className="font-medium text-text bg-bg p-2 rounded-lg border border-border/50 block">
                            {hold.resolution_note}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

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
        </>
      )}
    </div>
  );
}
