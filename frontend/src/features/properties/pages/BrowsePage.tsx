import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { Search, MapPin, Building, SlidersHorizontal, RotateCcw, ChevronLeft, ChevronRight } from "lucide-react";

import { propertyService } from "../../../services/propertyService";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Input } from "../../../components/ui/Input";
import { Label } from "../../../components/ui/Label";
import { Badge } from "../../../components/ui/Badge";
import { SkeletonCard } from "../../../components/common/SkeletonCard";
import { EmptyState } from "../../../components/common/EmptyState";
import { PropertyType, GenderPreference } from "../../../types/enums";

export default function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Load initial filter states from URL search params
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [debouncedSearch, setDebouncedSearch] = useState(searchParams.get("search") || "");
  const [city, setCity] = useState(searchParams.get("city") || "");
  const [propertyType, setPropertyType] = useState(searchParams.get("type") || "");
  const [genderPreference, setGenderPreference] = useState(searchParams.get("gender") || "");
  const [priceMin, setPriceMin] = useState(searchParams.get("price_min") || "");
  const [priceMax, setPriceMax] = useState(searchParams.get("price_max") || "");
  const [page, setPage] = useState(parseInt(searchParams.get("page") || "1", 10));

  // Sync debounced search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setPage(1); // reset to page 1 on search
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Sync search parameters back to URL
  useEffect(() => {
    const params: Record<string, string> = {};
    if (debouncedSearch) params.search = debouncedSearch;
    if (city) params.city = city;
    if (propertyType) params.type = propertyType;
    if (genderPreference) params.gender = genderPreference;
    if (priceMin) params.price_min = priceMin;
    if (priceMax) params.price_max = priceMax;
    if (page > 1) params.page = page.toString();

    setSearchParams(params, { replace: true });
  }, [debouncedSearch, city, propertyType, genderPreference, priceMin, priceMax, page, setSearchParams]);

  // Fetch properties via React Query
  const { data, isLoading, isError } = useQuery({
    queryKey: ["properties", debouncedSearch, city, propertyType, genderPreference, priceMin, priceMax, page],
    queryFn: async () => {
      const minVal = priceMin ? parseFloat(priceMin) : undefined;
      const maxVal = priceMax ? parseFloat(priceMax) : undefined;

      return propertyService.listProperties({
        search: debouncedSearch || undefined,
        city: city || undefined,
        property_type: propertyType || undefined,
        gender_preference: genderPreference || undefined,
        price_min: minVal,
        price_max: maxVal,
        status: "active",
        page,
        page_size: 9,
      });
    },
  });

  const clearFilters = () => {
    setSearchInput("");
    setDebouncedSearch("");
    setCity("");
    setPropertyType("");
    setGenderPreference("");
    setPriceMin("");
    setPriceMax("");
    setPage(1);
  };

  const properties = data?.data || [];
  const pagination = data?.pagination;

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 w-full bg-bg text-text">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight">Browse Accommodations</h1>
        <p className="mt-2 text-text-secondary text-sm">Find verified student living spaces, hostels, and flatshares tailored for you.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* ── Filters Sidebar ── */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-border bg-card shadow-xs">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="h-4 w-4 text-primary" />
                <CardTitle className="text-base font-bold">Filters</CardTitle>
              </div>
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs font-semibold text-text-secondary hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw className="h-3 w-3" />
                Reset
              </button>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              {/* City Filter */}
              <div className="space-y-1.5">
                <Label htmlFor="city-filter">City</Label>
                <Input
                  id="city-filter"
                  placeholder="e.g. Mumbai"
                  value={city}
                  onChange={(e) => {
                    setCity(e.target.value);
                    setPage(1);
                  }}
                />
              </div>

              {/* Property Type Filter */}
              <div className="space-y-1.5">
                <Label htmlFor="type-filter">Property Type</Label>
                <select
                  id="type-filter"
                  className="w-full flex h-10 rounded-md border border-input-border bg-input px-3 py-2 text-sm text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  value={propertyType}
                  onChange={(e) => {
                    setPropertyType(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Types</option>
                  <option value={PropertyType.PG}>PG</option>
                  <option value={PropertyType.HOSTEL}>Hostel</option>
                  <option value={PropertyType.FLAT}>Flat</option>
                  <option value={PropertyType.APARTMENT}>Apartment</option>
                </select>
              </div>

              {/* Gender Preference */}
              <div className="space-y-1.5">
                <Label htmlFor="gender-filter">Gender Preference</Label>
                <select
                  id="gender-filter"
                  className="w-full flex h-10 rounded-md border border-input-border bg-input px-3 py-2 text-sm text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  value={genderPreference}
                  onChange={(e) => {
                    setGenderPreference(e.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">Any</option>
                  <option value={GenderPreference.MALE}>Male Only</option>
                  <option value={GenderPreference.FEMALE}>Female Only</option>
                  <option value={GenderPreference.COED}>Co-ed</option>
                </select>
              </div>

              {/* Budget constraints */}
              <div className="space-y-2">
                <Label>Monthly Rent (Budget)</Label>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] text-text-secondary block">Min ₹</span>
                    <Input
                      type="number"
                      placeholder="Min"
                      value={priceMin}
                      onChange={(e) => {
                        setPriceMin(e.target.value);
                        setPage(1);
                      }}
                    />
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-text-secondary block">Max ₹</span>
                    <Input
                      type="number"
                      placeholder="Max"
                      value={priceMax}
                      onChange={(e) => {
                        setPriceMax(e.target.value);
                        setPage(1);
                      }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Properties Listing Grid ── */}
        <div className="lg:col-span-3 space-y-6">
          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-text-tertiary" />
            <Input
              type="text"
              placeholder="Search by college name, property title, or address..."
              className="pl-10 h-11 border-border shadow-xs"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>

          {/* Load results */}
          {isLoading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((id) => (
                <SkeletonCard key={id} />
              ))}
            </div>
          ) : isError ? (
            <div className="text-center py-20 border border-border rounded-xl bg-card">
              <p className="text-danger font-semibold">An error occurred while fetching properties.</p>
              <Button onClick={() => window.location.reload()} className="mt-4" size="sm">
                Retry Connection
              </Button>
            </div>
          ) : properties.length === 0 ? (
            <EmptyState
              title="No Accommodations Found"
              description="We couldn't find any stays matching your filters. Try clearing your filters or search something else."
              action={
                <Button onClick={clearFilters} variant="outline" size="sm">
                  Clear All Filters
                </Button>
              }
            />
          ) : (
            <>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {properties.map((property) => (
                  <Card key={property.id} className="group overflow-hidden border-border bg-card shadow-sm hover:shadow-md transition-all">
                    {/* Cover image */}
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
                          <span className="text-xs mt-2">No Image</span>
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
                    <CardHeader className="p-4">
                      <div className="flex items-center gap-1 text-xs text-text-secondary mb-1">
                        <MapPin className="h-3 w-3 text-primary" />
                        <span className="truncate">{property.city}, {property.state}</span>
                      </div>
                      <CardTitle className="text-lg font-bold line-clamp-1 group-hover:text-primary transition-colors">
                        {property.name}
                      </CardTitle>
                    </CardHeader>

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

                    {/* Card Footer */}
                    <CardFooter className="flex items-center justify-between p-4 border-t border-border bg-bg-secondary/40">
                      <div>
                        <span className="text-[10px] text-text-secondary block">Monthly Rent</span>
                        <span className="text-base font-bold text-primary">
                          {property.min_price ? `₹${property.min_price.toLocaleString("en-IN")}` : "N/A"}
                        </span>
                      </div>
                      <Button size="sm" asChild>
                        <Link to={`/property/${property.id}`}>View Details</Link>
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>

              {/* ── Pagination controls ── */}
              {pagination && pagination.total_pages > 1 && (
                <div className="flex items-center justify-between border-t border-border pt-6 mt-8">
                  <p className="text-sm text-text-secondary">
                    Page <span className="font-semibold text-text">{page}</span> of{" "}
                    <span className="font-semibold text-text">{pagination.total_pages}</span>
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                      disabled={!pagination.has_prev}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((prev) => Math.min(prev + 1, pagination.total_pages))}
                      disabled={!pagination.has_next}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
