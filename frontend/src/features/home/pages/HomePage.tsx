import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, Navigate } from "react-router-dom";
import { Search, MapPin, Shield, CheckCircle2, ChevronRight, Building } from "lucide-react";

import { propertyService } from "../../../services/propertyService";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import styles from "./HomePage.module.css";

import { useAuthStore } from "../../../stores/authStore";

export default function HomePage() {
  const { isAuthenticated, user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  // Fetch latest 6 active properties
  const { data, isLoading } = useQuery({
    queryKey: ["featuredProperties"],
    queryFn: async () => {
      const response = await propertyService.listProperties({
        page: 1,
        page_size: 6,
        status: "active",
      });
      return response.data;
    },
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/properties?search=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate("/properties");
    }
  };

  const featuredListings = data || [];

  if (isAuthenticated && user?.role === "owner") {
    return <Navigate to="/owner/dashboard" replace />;
  }

  return (
    <div className={styles.container}>
      {/* ── Hero Section ── */}
      <section className={styles.heroSection}>
        <div className={styles.heroBgWrapper}>
          <div className={styles.heroBgShape} />
        </div>

        <div className={styles.heroContent}>
          <Badge variant="outline" className={styles.heroBadge}>
            ✨ Real-time Student Housing Reservations
          </Badge>
          <h1 className={styles.heroTitle}>
            Premium Student Accommodations, <span className={styles.heroTitleHighlight}>Simplified.</span>
          </h1>
          <p className={styles.heroSubtitle}>
            StaySync connects students with verified high-quality PGs, hostels, and shared flats. Discover, save, and hold beds instantly in real-time.
          </p>

          {/* Search form bar */}
          <form onSubmit={handleSearchSubmit} className={styles.searchForm}>
            <div className={styles.searchInputWrapper}>
              <Search className={styles.searchIcon} />
              <Input
                type="text"
                placeholder="Search by city, state, or property name..."
                className={styles.searchInput}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button type="submit" size="lg" className={styles.searchBtn}>
              Search Stays
            </Button>
          </form>

          {/* Popular Cities */}
          <div className={styles.popularCities}>
            <span>Popular Cities:</span>
            {["Mumbai", "Delhi", "Bangalore", "Pune"].map((city) => (
              <button
                key={city}
                type="button"
                onClick={() => navigate(`/properties?search=${encodeURIComponent(city)}`)}
                className={styles.cityBtn}
              >
                {city}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Value Props / Features ── */}
      <section className={styles.featuresSection}>
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIconWrapper}>
              <Shield className={styles.featureIcon} />
            </div>
            <h3 className={styles.featureTitle}>Verified Listings</h3>
            <p className={styles.featureDesc}>
              Every listed PG and flat undergoes verification checkpoints, ensuring security, safety, and amenities accuracy.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIconWrapper}>
              <CheckCircle2 className={styles.featureIcon} />
            </div>
            <h3 className={styles.featureTitle}>Instant Bed Holds</h3>
            <p className={styles.featureDesc}>
              Secure your bed immediately with a live hold reservation while wrapping up document steps. No deposit loops.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.featureIconWrapper}>
              <Building className={styles.featureIcon} />
            </div>
            <h3 className={styles.featureTitle}>Flexible Formats</h3>
            <p className={styles.featureDesc}>
              Choose sharing types, PG amenities lists, and gender preferences. Tailored specifically for student workloads.
            </p>
          </div>
        </div>
      </section>

      {/* ── Featured Properties ── */}
      <section className={styles.propertiesSection}>
        <div className={styles.propertiesContainer}>
          <div className={styles.propertiesHeader}>
            <div>
              <h2 className={styles.propertiesTitle}>Featured Accommodations</h2>
              <p className={styles.propertiesSubtitle}>Handpicked premium properties with live bed availability</p>
            </div>
            <Button variant="outline" asChild className={styles.browseBtn}>
              <Link to="/properties">
                Browse All
                <ChevronRight className={styles.browseBtnIcon} />
              </Link>
            </Button>
          </div>

          {isLoading ? (
            <div className={styles.loadingWrapper}>
              <LoadingSpinner size="lg" />
            </div>
          ) : featuredListings.length === 0 ? (
            <div className={styles.emptyState}>
              <Building className={styles.emptyIcon} />
              <h3 className={styles.emptyTitle}>No active listings available</h3>
              <p className={styles.emptyDesc}>Check back later or check draft properties.</p>
            </div>
          ) : (
            <div className={styles.propertiesGrid}>
              {featuredListings.map((property) => (
                <Card key={property.id} className="group overflow-hidden border-border bg-card shadow-sm hover:shadow-md transition-shadow">
                  {/* Property Image Cover */}
                  <div className="relative aspect-[16/10] overflow-hidden bg-bg-tertiary">
                    {property.primary_image_url ? (
                      <img
                        src={property.primary_image_url}
                        alt={property.name}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="flex h-full w-full flex-col items-center justify-center text-text-tertiary">
                        <Building className="h-12 w-12 stroke-[1.5]" />
                        <span className="text-xs mt-2">No Image Provided</span>
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

                  {/* Card Content */}
                  <CardHeader className="p-5">
                    <div className="flex items-center gap-1 text-xs text-text-secondary mb-1">
                      <MapPin className="h-3 w-3 text-primary" />
                      <span>{property.city}, {property.state}</span>
                    </div>
                    <CardTitle className="text-xl font-bold line-clamp-1 group-hover:text-primary transition-colors">
                      {property.name}
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="px-5 pb-5">
                    <div className="flex items-center justify-between text-sm mb-4">
                      <span className="text-text-secondary">Bed Capacity:</span>
                      <span className="font-semibold text-text">
                        {property.available_beds} vacant / {property.total_beds} total
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-bg-tertiary overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{
                          width: `${(property.total_beds > 0 ? (property.total_beds - property.available_beds) / property.total_beds : 0) * 100}%`,
                        }}
                      />
                    </div>
                  </CardContent>

                  {/* Card Footer */}
                  <CardFooter className="flex items-center justify-between p-5 border-t border-border bg-bg-secondary/50">
                    <div>
                      <span className="text-xs text-text-secondary block">Monthly Rent</span>
                      <span className="text-lg font-bold text-primary">
                        {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}{" "}
                        <span className="text-xs font-normal text-text-secondary">onwards</span>
                      </span>
                    </div>
                    <Button size="sm" asChild>
                      <Link to={`/property/${property.id}`}>View Details</Link>
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── CTA Portal Banner ── */}
      <section className={styles.ctaSection}>
        <div className={styles.ctaCard}>
          <div className={styles.ctaBg} />
          <h2 className={styles.ctaTitle}>Are you a property manager?</h2>
          <p className={styles.ctaDesc}>
            Reach thousands of college students. List your hostels, PGs, or apartments on StaySync, and manage bookings and holds seamlessly.
          </p>
          <div className={styles.ctaActions}>
            <Button size="lg" variant="outline" className={styles.ctaBtn} asChild>
              <Link to="/register?role=owner">List Your Stays</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
