import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, IndianRupee, Layers, Sparkles, ArrowRight, TrendingUp, Users } from "lucide-react";

import { useAuthStore } from "../../../stores/authStore";
import { dashboardService } from "../../../services/dashboardService";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../../components/ui/Card";
import { Button } from "../../../components/ui/Button";
import { Badge } from "../../../components/ui/Badge";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

export default function OwnerDashboard() {
  const { user } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["ownerDashboardData"],
    queryFn: () => dashboardService.getOwnerDashboardData(),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20 min-h-[50vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const metrics = data || {
    listings_count: 0,
    total_beds: 0,
    occupied_beds: 0,
    occupied_bed_percentage: 0,
    revenue_projection: 0,
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-2">
      {/* Welcome Banner */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-primary/10 via-primary-dark/5 to-bg-secondary p-6 md:p-8 border border-primary/20">
        <div className="absolute inset-y-0 right-0 -z-10 w-full max-w-xl opacity-20 blur-2xl">
          <div className="aspect-[1000/600] w-full bg-gradient-to-tr from-primary to-primary-light" />
        </div>
        <div className="max-w-2xl">
          <Badge variant="outline" className="mb-3 border-primary/30 text-primary bg-primary/5">
            Owner Portal
          </Badge>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl font-sans">
            Welcome back, <span className="text-primary">{user?.profile?.full_name || "Manager"}</span>!
          </h1>
          <p className="mt-2 text-sm text-text-secondary leading-relaxed">
            Monitor real-time occupant density, track monthly revenues, and configure inventory properties from your administrative hub.
          </p>
        </div>
      </div>

      {/* Analytics widgets grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Properties */}
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">My Properties</span>
              <div className="text-3xl font-extrabold text-text mt-1">{metrics.listings_count}</div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Building2 className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-xs text-text-secondary">
            <Link to="/owner/properties" className="text-primary font-semibold hover:underline inline-flex items-center gap-0.5">
              Manage Properties <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* Occupancy Rate */}
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Occupancy Rate</span>
              <div className="text-3xl font-extrabold text-text mt-1">{metrics.occupied_bed_percentage}%</div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
              <Users className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 space-y-2">
            <div className="h-1.5 w-full rounded-full bg-bg-tertiary overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${metrics.occupied_bed_percentage}%` }} />
            </div>
            <div className="text-[10px] text-text-secondary flex justify-between">
              <span>{metrics.occupied_beds} / {metrics.total_beds} beds filled</span>
            </div>
          </CardContent>
        </Card>

        {/* Monthly Revenue Projection */}
        <Card className="border-border bg-card shadow-xs sm:col-span-2 lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Est. Monthly Revenue</span>
              <div className="text-3xl font-extrabold text-primary mt-1">
                ₹{metrics.revenue_projection.toLocaleString("en-IN")}
              </div>
            </div>
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
              <IndianRupee className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent className="pt-2 text-xs text-text-secondary flex items-center gap-1">
            <TrendingUp className="h-3.5 w-3.5 text-emerald-600" />
            <span>Calculated from filled bed minimum rental rates.</span>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Fast actions and checklist */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-lg font-bold">Quick Administrative Actions</CardTitle>
              <CardDescription className="text-xs">Manage properties and inspect check-in activities</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-2">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="p-4 rounded-xl border border-border bg-bg-secondary/30 flex flex-col justify-between">
                  <div className="space-y-1 mb-4">
                    <h4 className="text-sm font-bold text-text">Create Property</h4>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      Launch the multi-step wizard to upload images, check-mark amenities, and define rooms or beds.
                    </p>
                  </div>
                  <Button size="sm" asChild className="w-full">
                    <Link to="/owner/properties">List New Stay</Link>
                  </Button>
                </div>

                <div className="p-4 rounded-xl border border-border bg-bg-secondary/30 flex flex-col justify-between">
                  <div className="space-y-1 mb-4">
                    <h4 className="text-sm font-bold text-text">Properties Catalog</h4>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      Edit details, delete draft listings, and toggle active status flags on your accommodations.
                    </p>
                  </div>
                  <Button size="sm" variant="outline" asChild className="w-full">
                    <Link to="/owner/properties">Inspect Catalog</Link>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right 1 Column: Summary details */}
        <div className="space-y-6">
          <Card className="border-border bg-card">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                Live Status Reminders
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="flex gap-3 text-xs leading-relaxed">
                <div className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                  <Layers className="h-3 w-3" />
                </div>
                <div>
                  <span className="font-bold text-text block">Inventory Setup</span>
                  <span className="text-text-secondary block mt-0.5">
                    Make sure to specify floors and room sharing details so students can select beds.
                  </span>
                </div>
              </div>

              <div className="flex gap-3 text-xs leading-relaxed">
                <div className="h-5 w-5 rounded-full bg-amber-500/10 text-amber-600 flex items-center justify-center shrink-0 mt-0.5">
                  < IndianRupee className="h-3 w-3" />
                </div>
                <div>
                  <span className="font-bold text-text block">Hold Expiration Timers</span>
                  <span className="text-text-secondary block mt-0.5">
                    Beds held by students auto-expire or require manual check-ins (integrated in Phase 2).
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
