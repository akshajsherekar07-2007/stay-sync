import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, Plus, Edit, Trash2, Power, PowerOff, MapPin, Eye } from "lucide-react";
import { toast } from "sonner";

import { ownerPropertyService } from "../../../services/ownerPropertyService";
import { Card, CardContent } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { EmptyState } from "../../../components/common/EmptyState";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function ManagePropertiesPage() {
  const queryClient = useQueryClient();
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [isUpdatingStatusId, setIsUpdatingStatusId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["ownedProperties"],
    queryFn: () => ownerPropertyService.listOwnedProperties(),
  });

  const ownedProperties = data?.data || [];

  const handleToggleStatus = async (id: string, currentStatus: string) => {
    setIsUpdatingStatusId(id);
    const newStatus = currentStatus === "active" ? "inactive" : "active";
    try {
      await ownerPropertyService.updatePropertyStatus(id, newStatus);
      toast.success(`Property set to ${newStatus}.`);
      queryClient.invalidateQueries({ queryKey: ["ownedProperties"] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
    } catch (err) {
      toast.error("Failed to update status.");
    } finally {
      setIsUpdatingStatusId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this property? This action is irreversible.")) {
      return;
    }
    setIsDeletingId(id);
    try {
      await ownerPropertyService.deleteProperty(id);
      toast.success("Property deleted successfully.");
      queryClient.invalidateQueries({ queryKey: ["ownedProperties"] });
      queryClient.invalidateQueries({ queryKey: ["ownerDashboardData"] });
    } catch (err) {
      toast.error("Failed to delete property.");
    } finally {
      setIsDeletingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return <Badge variant="success" className="text-white capitalize">{status}</Badge>;
      case "inactive":
        return <Badge variant="secondary" className="capitalize">{status}</Badge>;
      case "draft":
        return <Badge variant="outline" className="border-amber-500 text-amber-600 bg-amber-500/5 capitalize">{status}</Badge>;
      case "pending_review":
        return <Badge variant="warning" className="text-white capitalize">Pending Review</Badge>;
      default:
        return <Badge variant="default" className="capitalize">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[50vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-2">
      {/* Header and Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">My Properties</h1>
          <p className="text-text-secondary text-sm mt-1">
            Manage your listed student accommodations, track bed holds, and toggle status configurations.
          </p>
        </div>
        <Button asChild className="flex items-center gap-1.5 self-start sm:self-auto font-semibold">
          <Link to="/owner/properties/create">
            <Plus className="h-4 w-4" />
            Add New Property
          </Link>
        </Button>
      </div>

      {ownedProperties.length === 0 ? (
        <EmptyState
          icon={<Building2 className="h-10 w-10 text-text-tertiary" />}
          title="No properties listed yet"
          description="Create your first student accommodation listing (PG, Flat, Hostel) to reach students."
          action={
            <Button asChild>
              <Link to="/owner/properties/create">List Your Stay</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-4">
          {ownedProperties.map((property) => (
            <Card key={property.id} className="overflow-hidden border border-border bg-card shadow-xs transition-colors hover:border-border/80">
              <CardContent className="p-4 sm:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
                
                {/* Visual Thumbnail & Metadata */}
                <div className="flex gap-4 items-start sm:items-center min-w-0">
                  <div className="relative w-20 h-16 sm:w-24 sm:h-18 rounded-lg overflow-hidden bg-bg-tertiary shrink-0 border border-border/40">
                    {property.primary_image_url ? (
                      <img src={property.primary_image_url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <Building2 className="h-6 w-6 text-text-tertiary m-auto absolute inset-0" />
                    )}
                  </div>
                  
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <h3 className="text-base font-bold text-text truncate max-w-sm sm:max-w-md">
                        {property.name}
                      </h3>
                      {getStatusBadge(property.status)}
                    </div>
                    
                    <div className="flex items-center gap-1 text-xs text-text-secondary">
                      <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
                      <span className="truncate">{property.city}, {property.state}</span>
                    </div>

                    <div className="text-xs text-text-secondary flex gap-3 flex-wrap">
                      <span>Rent Range: <span className="font-semibold text-text">₹{property.min_price?.toLocaleString("en-IN") || "N/A"}+</span></span>
                      <span>Beds: <span className="font-semibold text-text">{property.available_beds} vacant / {property.total_beds} total</span></span>
                    </div>
                  </div>
                </div>

                {/* Operations / Actions */}
                <div className="flex flex-wrap items-center gap-2 w-full md:w-auto border-t md:border-t-0 pt-3 md:pt-0 border-border/50 justify-end shrink-0">
                  {/* Public View Link */}
                  <Button variant="outline" size="sm" asChild className="flex items-center gap-1">
                    <Link to={`/property/${property.id}`}>
                      <Eye className="h-4 w-4" />
                      View Public
                    </Link>
                  </Button>

                  {/* Toggle Active Status */}
                  <Button
                    variant="outline"
                    size="sm"
                    className={`flex items-center gap-1 cursor-pointer ${
                      property.status === "active"
                        ? "border-amber-500/30 text-amber-600 hover:bg-amber-500/5"
                        : "border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/5"
                    }`}
                    onClick={() => handleToggleStatus(property.id, property.status)}
                    disabled={isUpdatingStatusId === property.id}
                  >
                    {property.status === "active" ? (
                      <>
                        <PowerOff className="h-4 w-4" />
                        Deactivate
                      </>
                    ) : (
                      <>
                        <Power className="h-4 w-4" />
                        Activate
                      </>
                    )}
                  </Button>

                  {/* Edit details */}
                  <Button variant="outline" size="sm" asChild className="flex items-center gap-1">
                    <Link to={`/owner/properties/${property.id}/edit`}>
                      <Edit className="h-4 w-4" />
                      Edit
                    </Link>
                  </Button>

                  {/* Soft Delete */}
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-danger/30 text-danger hover:bg-danger/5 hover:text-danger cursor-pointer"
                    onClick={() => handleDelete(property.id)}
                    disabled={isDeletingId === property.id}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
