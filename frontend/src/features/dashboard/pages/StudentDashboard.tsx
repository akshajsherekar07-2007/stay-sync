import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Heart, Building2, ArrowRight, Bed, Clock } from "lucide-react";

import { useAuthStore } from "../../../stores/authStore";
import { dashboardService } from "../../../services/dashboardService";
import { waitlistService } from "../../../services/waitlistService";
import { holdService } from "../../../services/holdService";
import { WaitlistCard } from "../components/WaitlistCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["studentDashboardData"],
    queryFn: () => dashboardService.getStudentDashboardData(),
  });

  const { data: waitlistsData, isLoading: isWaitlistsLoading } = useQuery({
    queryKey: ["myWaitlists"],
    queryFn: () => waitlistService.getMyWaitlists(),
  });

  const { data: holdsData, isLoading: isHoldsLoading } = useQuery({
    queryKey: ["myHolds"],
    queryFn: () => holdService.listMyHolds(),
  });

  if (isLoading || isWaitlistsLoading || isHoldsLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[50vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Find active holds based on status "approved" (which means actively held)
  const allHolds = holdsData?.data || [];
  const activeOrPendingHolds = allHolds.filter(h => h.status === "pending" || h.status === "approved");
  const activeHoldsCount = activeOrPendingHolds.length;
  
  // Override dashboard data active_holds_count with real data
  const activeHolds = activeHoldsCount || data?.active_holds_count || 0;
  const savedProperties = data?.saved_properties || [];
  const waitlists = waitlistsData?.data || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-2">
      {/* Welcome Banner */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-primary/10 via-primary-dark/5 to-bg-secondary p-6 md:p-8 border border-primary/20">
        <div className="absolute inset-y-0 right-0 -z-10 w-full max-w-xl opacity-20 blur-2xl">
          <div className="aspect-[1000/600] w-full bg-gradient-to-tr from-primary to-primary-light" />
        </div>
        <div className="max-w-2xl">
          <Badge variant="outline" className="mb-3 border-primary/30 text-primary bg-primary/5">
            Student Account
          </Badge>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Welcome back, <span className="text-primary">{user?.profile?.full_name || "Student"}</span>!
          </h1>
          <p className="mt-2 text-sm text-text-secondary leading-relaxed">
            Manage your accommodation search, monitor wishlists, and request bed holds directly from your dashboard hub.
          </p>
        </div>
      </div>

      {/* Metrics Widgets */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Active Holds widget */}
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Active Holds</span>
              <div className="text-3xl font-extrabold text-text mt-1">{activeHolds}</div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-amber-500/10 text-amber-600">
              <Clock className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-xs text-text-secondary">
            {activeHolds > 0 ? (
              <span className="text-amber-600 font-medium">You have an active bed hold reservation.</span>
            ) : (
              <span>You have no active bed holds. Holds can be requested on vacant beds.</span>
            )}
          </CardContent>
        </Card>

        {/* Wishlist widget */}
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Saved Properties</span>
              <div className="text-3xl font-extrabold text-text mt-1">{savedProperties.length}</div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-danger/10 text-danger">
              <Heart className="h-5 w-5 fill-danger/10" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-xs text-text-secondary">
            <Link to="/saved-properties" className="text-primary font-semibold hover:underline inline-flex items-center gap-0.5">
              View Wishlist <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* Verified Catalog Link widget */}
        <Card className="border-border bg-card shadow-xs sm:col-span-2 lg:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Stays Catalog</span>
              <div className="text-lg font-bold text-text mt-1">Browse Verified PGs</div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Building2 className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-xs text-text-secondary">
            <Link to="/properties" className="text-primary font-semibold hover:underline inline-flex items-center gap-0.5">
              Browse Listings <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Hold Reminders & Wishlist quick links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Hold Status Overview (Phase 2 stub) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-lg font-bold">Active Holds Summary</CardTitle>
              <CardDescription className="text-xs">Temporary bed reservations awaiting complete check-in</CardDescription>
            </CardHeader>
            <CardContent className="py-8 text-center bg-bg-secondary/30 border-t border-border/50">
              <div className="max-w-md mx-auto space-y-4">
                {activeOrPendingHolds.length > 0 ? (
                  <div className="space-y-4">
                    {activeOrPendingHolds.slice(0, 2).map((hold) => (
                      <div key={hold.id} className="p-4 bg-bg border border-border rounded-lg text-left">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-bold text-sm">Hold Status: <Badge variant={hold.status === "approved" ? "success" : "warning"} className="ml-2 text-white capitalize">{hold.status}</Badge></span>
                          <span className="text-xs text-text-secondary">Expires: {hold.expires_at ? new Date(hold.expires_at).toLocaleString() : "N/A"}</span>
                        </div>
                        <p className="text-xs text-text-secondary">
                          Hold duration: {hold.hold_duration_hours} hours.
                        </p>
                      </div>
                    ))}
                    <div className="pt-2">
                      <Button asChild size="sm" variant="outline">
                        <Link to="/dashboard/holds">View All Holds</Link>
                      </Button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="h-12 w-12 flex items-center justify-center rounded-full bg-amber-500/10 text-amber-600 mx-auto">
                      <Bed className="h-6 w-6" />
                    </div>
                    <h3 className="text-base font-bold text-text">No Bed Holds Requested</h3>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      You currently have no active or pending bed holds. Browse the catalog to request a bed hold.
                    </p>
                    <div className="pt-2">
                      <Button asChild size="sm">
                        <Link to="/properties">Search Stays</Link>
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Waitlist Section */}
          <div className="space-y-4 pt-4">
            <h3 className="text-lg font-bold text-text">My Waitlists</h3>
            {waitlists.length === 0 ? (
              <Card className="border-border bg-card">
                <CardContent className="py-8 text-center bg-bg-secondary/30">
                  <p className="text-sm text-text-secondary">You are not currently on any waitlists.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {waitlists.map((entry) => (
                  <WaitlistCard key={entry.id} entry={entry} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right 1 Column: Saved Stays Quick View */}
        <div className="space-y-6">
          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border/50">
              <div className="space-y-0.5">
                <CardTitle className="text-base font-bold">My Saved Stays</CardTitle>
                <CardDescription className="text-[10px]">Quick-access wishlist</CardDescription>
              </div>
              <Button size="sm" variant="ghost" asChild>
                <Link to="/saved-properties" className="text-xs font-semibold text-primary hover:underline">
                  View All
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="pt-4">
              {savedProperties.length === 0 ? (
                <div className="text-center py-8 text-xs text-text-tertiary">
                  <Heart className="h-8 w-8 text-text-tertiary mx-auto mb-2 opacity-50" />
                  No properties saved yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {savedProperties.slice(0, 4).map((property) => (
                    <div
                      key={property.id}
                      className="group flex gap-3 p-2.5 rounded-lg border border-border hover:border-text-secondary bg-bg-secondary/40 transition-colors"
                    >
                      {/* Image Thumbnail */}
                      <div className="relative w-16 h-12 rounded-md overflow-hidden bg-bg-tertiary shrink-0 border border-border/40">
                        {property.primary_image_url ? (
                          <img src={property.primary_image_url} alt="" className="h-full w-full object-cover" />
                        ) : (
                          <Building2 className="h-5 w-5 text-text-tertiary m-auto absolute inset-0" />
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex flex-col justify-between min-w-0 flex-grow text-xs">
                        <div>
                          <h4 className="font-bold text-text truncate group-hover:text-primary transition-colors">
                            <Link to={`/property/${property.id}`}>{property.name}</Link>
                          </h4>
                          <span className="text-[10px] text-text-secondary block">
                            {property.city}, {property.state}
                          </span>
                        </div>
                        <div className="flex justify-between items-center mt-1">
                          <span className="text-[10px] font-semibold text-primary">
                            ₹{property.min_price?.toLocaleString("en-IN") || "N/A"}
                          </span>
                          <span className="text-[9px] text-text-secondary">
                            {property.available_beds} vacant
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
