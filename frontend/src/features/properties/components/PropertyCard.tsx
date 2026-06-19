import { Link } from "react-router-dom";
import { MapPin, Building } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import type { PropertyListItem } from "../../../types/property";

interface PropertyCardProps {
  property: PropertyListItem;
}

export function PropertyCard({ property }: PropertyCardProps) {
  // Calculate fill percentage for bed availability
  const fillPercentage = property.total_beds > 0 
    ? ((property.total_beds - property.available_beds) / property.total_beds) * 100 
    : 0;
  
  const isAvailable = property.available_beds > 0;

  return (
    <Link to={`/property/${property.id}`} className="group block h-full outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-2xl active:scale-[0.98] transition-all duration-300">
      <Card className="overflow-hidden border-0 bg-white ring-1 ring-border/40 shadow-sm group-hover:shadow-2xl group-hover:-translate-y-1 transition-all duration-300 flex flex-col h-full rounded-2xl">
        {/* Cover image area - Airbnb Style (4/3 aspect ratio) */}
        <div className="relative aspect-[4/3] overflow-hidden bg-bg-tertiary">
          {property.primary_image_url ? (
            <img
              src={property.primary_image_url}
              alt={property.name}
              className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full flex-col items-center justify-center text-text-tertiary bg-bg-secondary">
              <Building className="h-10 w-10 stroke-[1.5] mb-2 text-text-tertiary/50" />
            </div>
          )}
          
          {/* Subtle gradient overlay at the top for badge legibility */}
          <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/40 to-transparent pointer-events-none" />

          {/* Badges */}
          <div className="absolute top-4 left-4 flex flex-col gap-2 z-10 items-start">
            <Badge className="capitalize font-semibold text-xs tracking-wide shadow-sm backdrop-blur-md bg-white/90 text-text border-none px-2.5 py-1">
              {property.property_type}
            </Badge>
          </div>
          
          <div className="absolute top-4 right-4 flex z-10">
            <Badge variant="outline" className="capitalize shadow-sm backdrop-blur-md bg-black/60 text-white border-white/20 font-medium px-2.5 py-1">
              {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
            </Badge>
          </div>
        </div>

        {/* Card Content Area */}
        <CardHeader className="p-5 pb-3">
          <div className="flex justify-between items-start gap-4">
            <div className="flex-1">
              <CardTitle className="text-[17px] font-bold line-clamp-1 text-text group-hover:text-primary transition-colors duration-200">
                {property.name}
              </CardTitle>
              <div className="flex items-center gap-1 mt-1 text-[13px] text-text-secondary">
                <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
                <span className="truncate">{property.city}, {property.state}</span>
              </div>
            </div>
            
            {/* Price block - Right aligned */}
            <div className="text-right flex-shrink-0">
              <div className="text-lg font-extrabold text-text leading-none">
                {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
              </div>
              <div className="text-[11px] font-medium text-text-secondary mt-1">
                / mo
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="px-5 pb-5 text-sm flex-1 flex flex-col justify-end">
          {/* Minimal availability indicator */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-medium text-text-secondary">Availability</span>
            <span className="text-[13px] font-bold">
              {isAvailable ? (
                <span className="text-emerald-600">{property.available_beds} beds left</span>
              ) : (
                <span className="text-danger">Sold Out</span>
              )}
            </span>
          </div>
          
          <div className="h-1.5 w-full rounded-full bg-bg-tertiary overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${isAvailable ? 'bg-primary' : 'bg-danger'}`}
              style={{ width: `${isAvailable ? fillPercentage : 100}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
