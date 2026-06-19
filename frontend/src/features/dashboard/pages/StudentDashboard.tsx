import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Heart, Building2, ArrowRight, Bed, Clock, ShieldCheck, CalendarClock, Zap } from "lucide-react";

import { useAuthStore } from "../../../stores/authStore";
import { dashboardService } from "../../../services/dashboardService";
import { waitlistService } from "../../../services/waitlistService";
import { holdService } from "../../../services/holdService";
import { WaitlistCard } from "../components/WaitlistCard";
import { DashboardSkeleton } from "../../../components/common/DashboardSkeleton";

export default function StudentDashboard() {
  const { user } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["studentDashboardData"],
    queryFn: () => dashboardService.getStudentDashboardData(),
  });

  const { data: waitlistsData, isLoading: isWaitlistsLoading } = useQuery({
    queryKey: ["myWaitlists", user?.id],
    queryFn: () => waitlistService.getMyWaitlists(),
    enabled: !!user?.id,
  });

  const { data: holdsData, isLoading: isHoldsLoading } = useQuery({
    queryKey: ["myHolds", user?.id],
    queryFn: () => holdService.listMyHolds(),
    enabled: !!user?.id,
  });

  if (isLoading || isWaitlistsLoading || isHoldsLoading) {
    return <DashboardSkeleton />;
  }

  const allHolds = holdsData?.data || [];
  const activeOrPendingHolds = allHolds.filter(h => h.status === "pending" || h.status === "approved");
  const activeHoldsCount = activeOrPendingHolds.length;
  
  const activeHolds = activeHoldsCount || data?.active_holds_count || 0;
  const savedProperties = data?.saved_properties || [];
  const waitlists = waitlistsData?.data || [];

  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden mb-4">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text mb-2">
          Overview
        </h1>
        <p className="text-sm text-text-secondary">
          Manage your accommodation search, waitlists, and bed reservations.
        </p>
      </div>

      {/* Metrics Widgets (Supabase/Stripe Style) */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Active Holds */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Active Holds</span>
            <Clock className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black tracking-tight text-text">{activeHolds}</span>
          </div>
          <div className="mt-4 text-xs font-medium text-text-secondary">
            {activeHolds > 0 ? (
              <span className="text-amber-600 font-bold">You have active reservations</span>
            ) : (
              <span>Ready to hold a bed</span>
            )}
          </div>
        </div>

        {/* Wishlist widget */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Saved Properties</span>
            <Heart className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black tracking-tight text-text">{savedProperties.length}</span>
          </div>
          <Link to="/saved-properties" className="text-xs font-semibold text-primary hover:text-primary-dark mt-4 inline-flex items-center gap-1 group">
            View wishlist <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>

        {/* Catalog Link */}
        <div className="bg-white rounded-2xl p-6 border border-border/60 shadow-sm hover:shadow-md transition-shadow sm:col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Stays Catalog</span>
            <Building2 className="h-4 w-4 text-text-tertiary" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black tracking-tight text-text">Browse PGs</span>
          </div>
          <Link to="/properties" className="text-xs font-semibold text-primary hover:text-primary-dark mt-4 inline-flex items-center gap-1 group">
            View all listings <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>

      {/* Main Grid: Holds, Waitlist, Wishlist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns: Holds & Waitlist */}
        <div className="lg:col-span-2 space-y-10">
          
          <section>
            <h2 className="text-xl font-bold tracking-tight text-text mb-4">Active Holds Summary</h2>
            <div className="bg-white rounded-2xl border border-border/60 shadow-sm p-6 overflow-hidden">
              {activeOrPendingHolds.length > 0 ? (
                <div className="space-y-4">
                  {activeOrPendingHolds.slice(0, 2).map((hold) => (
                    <div key={hold.id} className="p-5 bg-bg-secondary hover:bg-white hover:shadow-md border border-border/40 transition-all duration-300 rounded-[20px] flex items-center justify-between group">
                      <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center shadow-sm ${
                          hold.status === 'approved' ? 'bg-emerald-50 text-emerald-600 border border-emerald-500/20' : 'bg-amber-50 text-amber-600 border border-amber-500/20'
                        }`}>
                          <CalendarClock className="h-5 w-5" />
                        </div>
                        <div>
                          <span className="font-bold text-sm text-text block mb-1">
                            Status: 
                            <span className={`ml-2 text-xs uppercase tracking-wider px-2 py-0.5 rounded font-bold ${hold.status === "approved" ? "bg-emerald-500 text-white" : "bg-amber-500 text-white"}`}>
                              {hold.status}
                            </span>
                          </span>
                          <span className="text-[11px] text-text-secondary font-medium">
                            Expires: <strong className="text-text">{hold.expires_at ? new Date(hold.expires_at).toLocaleDateString() : "N/A"}</strong>
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-[11px] text-text-secondary font-bold">
                          Duration: {hold.hold_duration_hours}h
                        </p>
                      </div>
                    </div>
                  ))}
                  <div className="pt-2">
                    <Link to="/dashboard/holds" className="text-sm font-semibold text-primary hover:underline">
                      View all holds
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="text-center py-10">
                  <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-bg-secondary text-text-tertiary mx-auto mb-4 border border-border/60">
                    <Bed className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-bold text-text">No Bed Holds Requested</h3>
                  <p className="text-xs text-text-secondary mt-1 max-w-sm mx-auto">
                    You currently have no active or pending bed holds.
                  </p>
                  <div className="mt-6">
                    <Link to="/properties" className="text-sm font-semibold text-white bg-text hover:bg-text/90 px-5 py-2.5 rounded-xl shadow-sm transition-all">
                      Search Stays
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Waitlist Section */}
          <section>
            <h2 className="text-xl font-bold tracking-tight text-text mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              My Waitlists
            </h2>
            {waitlists.length === 0 ? (
              <div className="bg-white rounded-2xl border border-border/60 shadow-sm p-12 text-center">
                <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-bg-secondary text-text-tertiary mx-auto mb-3 border border-border/60">
                  <Clock className="h-5 w-5" />
                </div>
                <h4 className="text-sm font-bold text-text mb-1">No Active Waitlists</h4>
                <p className="text-xs text-text-secondary font-medium">You are not currently on any waitlists.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {waitlists.map((entry) => (
                  <WaitlistCard key={entry.id} entry={entry} />
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Right 1 Column: Saved Stays & Notifications */}
        <div className="space-y-10">
          {/* Saved Stays */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold tracking-tight text-text">Saved Stays</h2>
              <Link to="/saved-properties" className="text-xs font-semibold text-primary hover:underline">
                View All
              </Link>
            </div>
            
            <div className="bg-white rounded-2xl border border-border/60 shadow-sm p-5">
              {savedProperties.length === 0 ? (
                <div className="text-center py-6">
                  <Heart className="h-8 w-8 text-text-tertiary mx-auto mb-3 opacity-30" />
                  <p className="text-xs text-text-secondary font-medium">No properties saved yet.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {savedProperties.slice(0, 3).map((property) => (
                    <div key={property.id} className="group flex gap-4 items-center">
                      <div className="relative w-14 h-14 rounded-xl overflow-hidden bg-bg-secondary shrink-0 border border-border/60">
                        {property.primary_image_url ? (
                          <img src={property.primary_image_url} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
                        ) : (
                          <Building2 className="h-5 w-5 text-text-tertiary m-auto absolute inset-0" />
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <h4 className="font-bold text-sm text-text truncate group-hover:text-primary transition-colors">
                          <Link to={`/property/${property.id}`} className="focus:outline-none before:absolute before:inset-0">
                            {property.name}
                          </Link>
                        </h4>
                        <span className="text-xs text-text-secondary block font-medium">
                          {property.city}, {property.state}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Account Alerts */}
          <section>
            <h2 className="text-xl font-bold tracking-tight text-text mb-4">System Alerts</h2>
            <div className="bg-white rounded-2xl border border-border/60 shadow-sm p-6 space-y-6">
              <div className="flex gap-4">
                <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0 shadow-sm border border-primary/10">
                  <Clock className="h-4 w-4" />
                </div>
                <div className="space-y-1 text-sm">
                  <Link to="/dashboard/holds" className="font-bold text-text hover:text-primary transition-colors block">
                    Check Reservation Status
                  </Link>
                  <span className="text-text-secondary text-xs block leading-relaxed">
                    Verify hold request expiration timers and approval messages.
                  </span>
                </div>
              </div>

              <div className="w-full h-px bg-border/60" />

              <div className="flex gap-4">
                <div className="h-8 w-8 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center shrink-0 shadow-sm border border-emerald-500/10">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                <div className="space-y-1 text-sm">
                  <Link to="/notifications" className="font-bold text-text hover:text-primary transition-colors block">
                    Recent Activity Log
                  </Link>
                  <span className="text-text-secondary text-xs block leading-relaxed">
                    View direct system notifications regarding check-in dates.
                  </span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
