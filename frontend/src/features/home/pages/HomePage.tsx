import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Search, MapPin, Shield, CheckCircle2, ChevronRight, Building } from "lucide-react";

import { propertyService } from "../../../services/propertyService";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function HomePage() {
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

  return (
    <div className="flex flex-col w-full pb-16 bg-bg text-text">
      {/* ── Hero Section ── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-primary-dark/5 to-bg py-20 lg:py-32 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-y-0 right-0 -z-10 w-full max-w-3xl opacity-20 dark:opacity-10 blur-3xl">
          <div className="aspect-[1155/678] w-[72.1875rem] bg-gradient-to-tr from-primary to-primary-light" />
        </div>

        <div className="mx-auto max-w-7xl text-center">
          <Badge variant="outline" className="mb-4 animate-fade-in border-primary/30 text-primary bg-primary/5 px-4 py-1">
            ✨ Real-time Student Housing Reservations
          </Badge>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl max-w-4xl mx-auto leading-tight">
            Premium Student Accommodations, <span className="bg-gradient-to-r from-primary to-primary-light bg-clip-text text-transparent">Simplified.</span>
          </h1>
          <p className="mt-6 text-lg text-text-secondary max-w-2xl mx-auto">
            StaySync connects students with verified high-quality PGs, hostels, and shared flats. Discover, save, and hold beds instantly in real-time.
          </p>

          {/* Search form bar */}
          <form onSubmit={handleSearchSubmit} className="mt-10 max-w-2xl mx-auto flex flex-col sm:flex-row gap-3 p-2 rounded-xl bg-card border border-border shadow-md">
            <div className="relative flex-grow">
              <Search className="absolute left-3 top-3 h-5 w-5 text-text-tertiary" />
              <Input
                type="text"
                placeholder="Search by city, state, or property name..."
                className="pl-10 border-none bg-transparent shadow-none focus-visible:ring-0"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button type="submit" size="lg" className="w-full sm:w-auto font-semibold">
              Search Stays
            </Button>
          </form>

          {/* Popular Cities */}
          <div className="mt-8 flex flex-wrap justify-center gap-2 text-sm text-text-secondary">
            <span>Popular Cities:</span>
            {["Mumbai", "Delhi", "Bangalore", "Pune"].map((city) => (
              <button
                key={city}
                type="button"
                onClick={() => navigate(`/properties?search=${encodeURIComponent(city)}`)}
                className="font-medium text-primary hover:underline hover:text-primary-dark transition-colors cursor-pointer"
              >
                {city}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── Value Props / Features ── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-y border-border bg-bg-secondary">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center text-center p-6 bg-card border border-border rounded-xl shadow-xs transition-transform hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                <Shield className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Verified Listings</h3>
              <p className="mt-2 text-sm text-text-secondary leading-relaxed">
                Every listed PG and flat undergoes verification checkpoints, ensuring security, safety, and amenities accuracy.
              </p>
            </div>
            <div className="flex flex-col items-center text-center p-6 bg-card border border-border rounded-xl shadow-xs transition-transform hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Instant Bed Holds</h3>
              <p className="mt-2 text-sm text-text-secondary leading-relaxed">
                Secure your bed immediately with a live hold reservation while wrapping up document steps. No deposit loops.
              </p>
            </div>
            <div className="flex flex-col items-center text-center p-6 bg-card border border-border rounded-xl shadow-xs transition-transform hover:-translate-y-1">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                <Building className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Flexible Formats</h3>
              <p className="mt-2 text-sm text-text-secondary leading-relaxed">
                Choose sharing types, PG amenities lists, and gender preferences. Tailored specifically for student workloads.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Featured Properties ── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight">Featured Accommodations</h2>
              <p className="mt-2 text-text-secondary">Handpicked premium properties with live bed availability</p>
            </div>
            <Button variant="outline" asChild className="mt-4 sm:mt-0 font-medium flex items-center gap-1 group">
              <Link to="/properties">
                Browse All
                <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center items-center py-20">
              <LoadingSpinner size="lg" />
            </div>
          ) : featuredListings.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-border rounded-xl bg-card">
              <Building className="mx-auto h-12 w-12 text-text-tertiary mb-3" />
              <h3 className="text-lg font-semibold">No active listings available</h3>
              <p className="text-text-secondary text-sm mt-1">Check back later or check draft properties.</p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
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
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 mt-10">
        <div className="rounded-2xl bg-gradient-to-r from-primary to-primary-dark p-8 sm:p-12 text-white shadow-xl text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent pointer-events-none" />
          <h2 className="text-3xl font-extrabold tracking-tight">Are you a property manager?</h2>
          <p className="mt-4 text-lg text-primary-light max-w-2xl mx-auto leading-relaxed">
            Reach thousands of college students. List your hostels, PGs, or apartments on StaySync, and manage bookings and holds seamlessly.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/15 cursor-pointer bg-transparent" asChild>
              <Link to="/register?role=owner">List Your Stays</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
