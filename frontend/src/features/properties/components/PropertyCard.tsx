import { Link } from "react-router-dom";
import { MapPin, Building } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/Card";
import type { PropertyListItem } from "../../../types/property";
import styles from "./PropertyCard.module.css";

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
    <Link to={`/property/${property.id}`} className={styles.link}>
      <Card className={styles.card}>
        {/* Cover image area - Airbnb Style (4/3 aspect ratio) */}
        <div className={styles.imageArea}>
          {property.primary_image_url ? (
            <img
              src={property.primary_image_url}
              alt={property.name}
              className={styles.image}
            />
          ) : (
            <div className={styles.emptyImage}>
              <Building className={styles.emptyIcon} />
            </div>
          )}
          
          {/* Subtle gradient overlay at the top for badge legibility */}
          <div className={styles.gradientOverlay} />

          {/* Badges */}
          <div className={styles.badgesTopLeft}>
            <div className={styles.typeBadge}>
              {property.property_type}
            </div>
          </div>
          
          <div className={styles.badgesTopRight}>
            <div className={styles.genderBadge}>
              {property.gender_preference === "coed" ? "Co-ed" : property.gender_preference}
            </div>
          </div>
        </div>

        {/* Card Content Area */}
        <CardHeader className={styles.header}>
          <div className={styles.headerContent}>
            <div className={styles.headerMain}>
              <CardTitle className={styles.title}>
                {property.name}
              </CardTitle>
              <div className={styles.location}>
                <MapPin className={styles.locationIcon} />
                <span className={styles.locationText}>{property.city}, {property.state}</span>
              </div>
            </div>
            
            {/* Price block - Right aligned */}
            <div className={styles.priceBlock}>
              <div className={styles.priceAmount}>
                {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
              </div>
              <div className={styles.priceUnit}>
                / mo
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className={styles.content}>
          {/* Minimal availability indicator */}
          <div className={styles.availabilityHeader}>
            <span className={styles.availabilityLabel}>Availability</span>
            <span className={styles.availabilityValue}>
              {isAvailable ? (
                <span className={styles.textAvailable}>{property.available_beds} beds left</span>
              ) : (
                <span className={styles.textSoldOut}>Sold Out</span>
              )}
            </span>
          </div>
          
          <div className={styles.barTrack}>
            <div
              className={`${styles.barFill} ${isAvailable ? styles.bgAvailable : styles.bgSoldOut}`}
              style={{ width: `${isAvailable ? fillPercentage : 100}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
