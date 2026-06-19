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
    <div className="space-y-10 w-full mx-auto pb-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text mb-2">
            My Properties
          </h1>
          <p className="text-sm text-text-secondary">
            Manage your listed student accommodations, track bed holds, and toggle status configurations.
          </p>
        </div>
        <Button asChild size="lg" className="shrink-0 shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5">
          <Link to="/owner/properties/create">
            <Plus className="h-5 w-5 mr-2" />
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
        <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
          <div className="divide-y divide-border/40">
            {ownedProperties.map((property) => (
              <div key={property.id} className="p-4 sm:p-6 hover:bg-bg-secondary/30 transition-colors flex flex-col lg:flex-row lg:items-center justify-between gap-6 group">
                
                {/* Visual Thumbnail & Metadata */}
                <div className="flex gap-4 sm:gap-6 items-start sm:items-center min-w-0">
                  <div className="relative w-24 h-16 sm:w-32 sm:h-20 rounded-xl overflow-hidden bg-bg-secondary shrink-0 border border-border/40 shadow-xs">
                    {property.primary_image_url ? (
                      <img src={property.primary_image_url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <Building2 className="h-8 w-8 text-text-tertiary m-auto absolute inset-0" />
                    )}
                  </div>
                  
                  <div className="min-w-0 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-text truncate">
                        {property.name}
                      </h3>
                      {getStatusBadge(property.status)}
                    </div>
                    
                    <div className="flex items-center gap-1.5 text-sm text-text-secondary">
                      <MapPin className="h-4 w-4 text-primary shrink-0" />
                      <span className="truncate">{property.city}, {property.state}</span>
                    </div>

                    <div className="text-sm text-text-secondary flex gap-4 flex-wrap">
                      <span>Rent Range: <span className="font-semibold text-text">₹{property.min_price?.toLocaleString("en-IN") || "N/A"}+</span></span>
                      <span className="text-border">|</span>
                      <span>Beds: <span className="font-semibold text-text">{property.available_beds}</span> vacant <span className="text-text-tertiary mx-1">/</span> {property.total_beds} total</span>
                    </div>
                  </div>
                </div>

                {/* Operations / Actions */}
                <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full lg:w-auto pt-2 lg:pt-0 shrink-0">
                  {/* Public View Link */}
                  <Button variant="outline" size="sm" asChild className="flex items-center gap-1.5 bg-bg hover:bg-bg-secondary text-text-secondary hover:text-text">
                    <Link to={`/property/${property.id}`}>
                      <Eye className="h-4 w-4" />
                      View
                    </Link>
                  </Button>

                  {/* Toggle Active Status */}
                  <Button
                    variant="outline"
                    size="sm"
                    className={`flex items-center gap-1.5 cursor-pointer bg-bg ${
                      property.status === "active"
                        ? "border-amber-500/30 text-amber-600 hover:bg-amber-500/5 hover:border-amber-500/50"
                        : "border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/5 hover:border-emerald-500/50"
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
                  <Button variant="outline" size="sm" asChild className="flex items-center gap-1.5 bg-bg hover:bg-bg-secondary text-text-secondary hover:text-text">
                    <Link to={`/owner/properties/${property.id}/edit`}>
                      <Edit className="h-4 w-4" />
                      Edit
                    </Link>
                  </Button>

                  {/* Soft Delete */}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-9 w-9 border-danger/30 text-danger hover:bg-danger/10 hover:border-danger/50 cursor-pointer bg-bg"
                    onClick={() => handleDelete(property.id)}
                    disabled={isDeletingId === property.id}
                    title="Delete Property"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
