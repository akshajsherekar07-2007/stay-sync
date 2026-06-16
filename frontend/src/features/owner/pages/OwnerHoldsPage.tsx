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

  const handleReject = (holdId: string) => {
    const reason = prompt("Please enter a reason for rejection:");
    if (reason !== null) {
      rejectMutation.mutate({ holdId, reason });
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/owner/dashboard">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold text-text">Manage Hold Requests</h1>
        </div>

        {!isPropertiesLoading && properties.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-text-secondary">Property:</span>
            <select
              className="px-3 py-2 bg-bg border border-border rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary"
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
          ) : holds.length === 0 ? (
            <Card className="bg-bg border-border text-center py-12 shadow-xs">
              <CardContent>
                <Clock className="h-12 w-12 text-text-tertiary mx-auto mb-4" />
                <h3 className="text-lg font-bold text-text">No Holds Found</h3>
                <p className="text-text-secondary mt-2">There are no hold requests for this property.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {holds.map((hold) => (
                <Card key={hold.id} className="bg-card border-border shadow-xs overflow-hidden">
                  <div className="flex flex-col md:flex-row md:items-center justify-between p-5 border-b border-border/50 bg-bg-secondary/20 gap-4">
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
                    {hold.status === HoldStatus.PENDING && (
                      <div className="flex items-center gap-2">
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
                      </div>
                    )}
                  </div>
                  <CardContent className="p-5">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="block text-text-secondary text-xs">Student ID</span>
                        <span className="font-semibold text-text text-xs font-mono">{hold.student_id.slice(0, 8)}...</span>
                      </div>
                      <div>
                        <span className="block text-text-secondary text-xs">Bed ID</span>
                        <span className="font-semibold text-text text-xs font-mono">{hold.bed_id.slice(0, 8)}...</span>
                      </div>
                      <div>
                        <span className="block text-text-secondary text-xs">Duration</span>
                        <span className="font-semibold text-text">{hold.hold_duration_hours} hours</span>
                      </div>
                      {hold.expires_at && (
                        <div>
                          <span className="block text-text-secondary text-xs">Expires At</span>
                          <span className="font-bold text-amber-600">
                            {new Date(hold.expires_at).toLocaleString()}
                          </span>
                        </div>
                      )}
                      {hold.resolution_note && (
                        <div className="col-span-2 md:col-span-4">
                          <span className="block text-text-secondary text-xs">Resolution Note</span>
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
        </>
      )}
    </div>
  );
}
