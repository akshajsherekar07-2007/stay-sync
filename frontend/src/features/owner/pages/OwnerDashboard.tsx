import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Building2, IndianRupee, Layers, Sparkles, ArrowRight, TrendingUp, Users, ShieldCheck, Clock } from "lucide-react";

import { dashboardService } from "../../../services/dashboardService";
import { DashboardSkeleton } from "../../../components/common/DashboardSkeleton";

export default function OwnerDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["ownerDashboardData"],
    queryFn: () => dashboardService.getOwnerDashboardData(),
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const metrics = data || {
    listings_count: 0,
    total_beds: 0,
    occupied_beds: 0,
    occupied_bed_percentage: 0,
    revenue_projection: 0,
  };

  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden mb-4">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text mb-2">
          Overview
        </h1>
        <p className="text-sm text-text-secondary">
          Monitor your portfolio performance and manage daily operations.
        </p>
      </div>

      {/* Analytics widgets grid - 4 metric cards (Supabase/Stripe Style) */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Properties */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Total Properties</span>
            <Building2 className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black tracking-tight text-text">{metrics.listings_count}</span>
          </div>
          <Link to="/owner/properties" className="text-xs font-semibold text-primary hover:text-primary-dark mt-4 inline-flex items-center gap-1 group">
            View catalog <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        {/* Occupancy Rate */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Occupancy Rate</span>
            <Users className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black tracking-tight text-text">{metrics.occupied_bed_percentage}%</span>
            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded flex items-center gap-0.5">
              <TrendingUp className="h-3 w-3" />
              Healthy
            </span>
          </div>
          <div className="mt-4 h-1.5 w-full rounded-full bg-bg-secondary overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full transition-all duration-1000 ease-out" style={{ width: `${metrics.occupied_bed_percentage}%` }} />
          </div>
        </div>

        {/* Occupied Beds */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Occupied Beds</span>
            <Layers className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black tracking-tight text-text">{metrics.occupied_beds}</span>
            <span className="text-sm font-semibold text-text-secondary">/ {metrics.total_beds}</span>
          </div>
          <div className="mt-4 text-xs font-medium text-text-secondary">
            <strong className="text-text">{metrics.total_beds - metrics.occupied_beds}</strong> beds available
          </div>
        </div>

        {/* Monthly Revenue Projection */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Projected Revenue</span>
            <IndianRupee className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-text-secondary">₹</span>
            <span className="text-4xl font-black tracking-tight text-text">
              {metrics.revenue_projection >= 1000 ? (metrics.revenue_projection / 1000).toFixed(1) + 'k' : metrics.revenue_projection}
            </span>
            <span className="text-sm font-medium text-text-secondary">/mo</span>
          </div>
          <div className="mt-4 text-xs font-medium text-text-secondary">
            Estimated from occupied beds
          </div>
        </div>
      </div>

      {/* Main Grid split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Fast actions */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold tracking-tight text-text mb-4">Administrative Actions</h2>
          
          <div className="grid gap-4 sm:grid-cols-3">
            {/* Action 1 */}
            <Link to="/owner/properties/create" className="group block bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md hover:border-primary/30 transition-all">
              <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-4">
                <Building2 className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-text group-hover:text-primary transition-colors">List New Property</h4>
              <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                Add a new property, setup rooms, and configure bed inventory.
              </p>
            </Link>

            {/* Action 2 */}
            <Link to="/owner/holds" className="group block bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md hover:border-amber-500/30 transition-all">
              <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-4">
                <Clock className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-text group-hover:text-amber-600 transition-colors">Review Holds</h4>
              <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                Approve or reject active bed hold requests from students.
              </p>
            </Link>

            {/* Action 3 */}
            <Link to="/owner/properties" className="group block bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md hover:border-text/30 transition-all">
              <div className="h-10 w-10 rounded-xl bg-bg-secondary text-text-secondary flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-text group-hover:text-text transition-colors">Manage Catalog</h4>
              <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                Edit existing listings, update photos, and toggle visibility.
              </p>
            </Link>
          </div>
        </div>

        {/* Right 1 Column: Summary details */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold tracking-tight text-text mb-4">System Alerts</h2>
          
          <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm space-y-6">
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 shadow-sm border border-primary/10">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <span className="text-sm font-bold text-text block">Inventory Setup</span>
                <span className="text-xs text-text-secondary block leading-relaxed">
                  Make sure to configure rooms and beds after listing a property so students can book.
                </span>
              </div>
            </div>

            <div className="w-full h-px bg-border/60" />

            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-amber-500/10 text-amber-600 flex items-center justify-center shrink-0 shadow-sm border border-amber-500/10">
                <Clock className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <span className="text-sm font-bold text-text block">Hold Expirations</span>
                <span className="text-xs text-text-secondary block leading-relaxed">
                  Pending bed holds automatically expire if not approved within 24 hours.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
