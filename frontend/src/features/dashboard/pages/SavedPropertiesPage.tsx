import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Heart, Building, MapPin, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { savedPropertyService } from "../../../services/savedPropertyService";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { EmptyState } from "../../../components/common/EmptyState";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function SavedPropertiesPage() {
  const queryClient = useQueryClient();
  const [isRemovingId, setIsRemovingId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["savedProperties"],
    queryFn: () => savedPropertyService.listSavedProperties(),
  });

  const savedListings = data?.data || [];

  const handleRemove = async (propertyId: string) => {
    setIsRemovingId(propertyId);
    try {
      await savedPropertyService.unsaveProperty(propertyId);
      toast.success("Removed from wishlist.");
      queryClient.invalidateQueries({ queryKey: ["savedProperties"] });
    } catch (err) {
      toast.error("Failed to remove property.");
    } finally {
      setIsRemovingId(null);
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
    <div className="space-y-6 w-full mx-auto pb-8">
      {/* Header Section */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Saved Properties</h1>
        <p className="text-text-secondary text-sm mt-1">
          A watchlist of accommodations you are interested in tracking or holding.
        </p>
      </div>

      {savedListings.length === 0 ? (
        <EmptyState
          icon={<Heart className="h-8 w-8 text-text-tertiary" />}
          title="Your wishlist is empty"
          description="Browse available properties and click the save icon to add stays to your watchlist."
          action={
            <Button asChild>
              <Link to="/properties">Browse Properties</Link>
            </Button>
          }
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {savedListings.map((property) => (
            <Card key={property.id} className="group overflow-hidden border-border bg-card shadow-sm hover:shadow-md transition-shadow">
              {/* Cover Image */}
              <div className="relative aspect-[16/10] overflow-hidden bg-bg-tertiary">
                {property.primary_image_url ? (
                  <img
                    src={property.primary_image_url}
                    alt={property.name}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="flex h-full w-full flex-col items-center justify-center text-text-tertiary">
                    <Building className="h-10 w-10 stroke-[1.5]" />
                    <span className="text-[10px] mt-2">No Image</span>
                  </div>
                )}

                <div className="absolute top-3 right-3 flex flex-col gap-1.5 items-end">
                  <Badge variant="success" className="capitalize text-white">
                    {property.property_type}
                  </Badge>
                  <Badge className="capitalize bg-black/70 text-white">
                    {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
                  </Badge>
                </div>
              </div>

              {/* Header */}
              <CardHeader className="p-4">
                <div className="flex items-center gap-1 text-[11px] text-text-secondary mb-1">
                  <MapPin className="h-3 w-3 text-primary" />
                  <span className="truncate">{property.city}, {property.state}</span>
                </div>
                <CardTitle className="text-lg font-bold line-clamp-1 group-hover:text-primary transition-colors">
                  {property.name}
                </CardTitle>
              </CardHeader>

              {/* Content */}
              <CardContent className="px-4 pb-4 text-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-text-secondary">Available Beds:</span>
                  <span className="font-semibold text-text">
                    {property.available_beds} vacant / {property.total_beds} total
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-bg-tertiary overflow-hidden">
                  <div
                    className="h-full bg-primary"
                    style={{
                      width: `${(property.total_beds > 0 ? (property.total_beds - property.available_beds) / property.total_beds : 0) * 100}%`,
                    }}
                  />
                </div>
              </CardContent>

              {/* Footer */}
              <CardFooter className="flex items-center justify-between p-4 border-t border-border bg-bg-secondary/40">
                <div>
                  <span className="text-[10px] text-text-secondary block">Monthly Rent</span>
                  <span className="text-base font-bold text-primary">
                    {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-danger/30 text-danger hover:bg-danger/5 hover:text-danger cursor-pointer p-2 h-9"
                    onClick={() => handleRemove(property.id)}
                    disabled={isRemovingId === property.id}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  <Button size="sm" asChild>
                    <Link to={`/property/${property.id}`}>View Stay</Link>
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
