import { useState } from "react";
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

  const [clearedWaitlists, setClearedWaitlists] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("student_cleared_waitlists");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const handleClearWaitlist = (waitlistId: string) => {
    const newCleared = [...clearedWaitlists, waitlistId];
    setClearedWaitlists(newCleared);
    localStorage.setItem("student_cleared_waitlists", JSON.stringify(newCleared));
  };

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
  const rawWaitlists = waitlistsData?.data || [];
  const waitlists = rawWaitlists.filter(w => !clearedWaitlists.includes(w.id));

  return (
    <div className="space-y-10 w-full mx-auto pb-8">
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

      {/* Main Content Area */}
      <div className="space-y-8 mt-8">
        
        {/* Active Holds Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold tracking-tight text-text">Active Holds Summary</h2>
            {activeOrPendingHolds.length > 0 && (
              <Link to="/dashboard/holds" className="text-sm font-semibold text-primary hover:text-primary-dark hover:underline">
                View all holds →
              </Link>
            )}
          </div>
          
          <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
            {activeOrPendingHolds.length > 0 ? (
              <div className="divide-y divide-border/40">
                {activeOrPendingHolds.slice(0, 3).map((hold) => (
                  <div key={hold.id} className="p-5 hover:bg-bg-secondary/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className={`h-12 w-12 rounded-2xl flex items-center justify-center shrink-0 shadow-sm ${
                        hold.status === 'approved' ? 'bg-emerald-50 text-emerald-600 border border-emerald-500/20' : 'bg-amber-50 text-amber-600 border border-amber-500/20'
                      }`}>
                        <CalendarClock className="h-6 w-6" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold text-text text-base">Bed Hold</span>
                          <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-bold ${hold.status === "approved" ? "bg-emerald-500 text-white" : "bg-amber-500 text-white"}`}>
                            {hold.status}
                          </span>
                        </div>
                        <div className="text-xs font-medium text-text-secondary">
                          Expires: <strong className="text-text">{hold.expires_at ? new Date(hold.expires_at).toLocaleDateString() : "N/A"}</strong>
                        </div>
                      </div>
                    </div>
                    <div className="text-left sm:text-right bg-bg-secondary/50 px-4 py-2 rounded-xl border border-border/50">
                      <p className="text-xs text-text-secondary font-semibold uppercase tracking-wider mb-0.5">
                        Duration
                      </p>
                      <p className="text-sm font-bold text-text">
                        {hold.hold_duration_hours} hours
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-bg-secondary text-text-tertiary mx-auto mb-4 border border-border/60">
                  <Bed className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-text">No Bed Holds Requested</h3>
                <p className="text-sm text-text-secondary mt-1 max-w-sm mx-auto">
                  You currently have no active or pending bed holds.
                </p>
                <div className="mt-6">
                  <Link to="/properties" className="text-sm font-bold text-white bg-text hover:bg-text/90 px-6 py-2.5 rounded-xl shadow-sm transition-all">
                    Search Stays
                  </Link>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* 2-Column Grid: Waitlists & Saved Stays */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Waitlists */}
          <section>
            <h2 className="text-xl font-bold tracking-tight text-text mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              My Waitlists
            </h2>
            <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
              {waitlists.length === 0 ? (
                <div className="p-10 text-center">
                  <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-bg-secondary text-text-tertiary mx-auto mb-3 border border-border/60">
                    <Clock className="h-5 w-5" />
                  </div>
                  <h4 className="text-sm font-bold text-text mb-1">No Active Waitlists</h4>
                  <p className="text-xs text-text-secondary font-medium">You are not currently on any waitlists.</p>
                </div>
              ) : (
                <div className="p-4 space-y-4 bg-bg/30">
                  {waitlists.map((entry) => (
                    <WaitlistCard 
                      key={entry.id} 
                      entry={entry} 
                      onClear={() => handleClearWaitlist(entry.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Saved Stays */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold tracking-tight text-text flex items-center gap-2">
                <Heart className="h-5 w-5 text-rose-500" />
                Saved Stays
              </h2>
              {savedProperties.length > 0 && (
                <Link to="/saved-properties" className="text-sm font-semibold text-primary hover:text-primary-dark hover:underline">
                  View All →
                </Link>
              )}
            </div>
            
            <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
              {savedProperties.length === 0 ? (
                <div className="p-10 text-center">
                  <Heart className="h-10 w-10 text-text-tertiary mx-auto mb-3 opacity-30" />
                  <p className="text-sm text-text-secondary font-medium">No properties saved yet.</p>
                </div>
              ) : (
                <div className="divide-y divide-border/40">
                  {savedProperties.slice(0, 3).map((property) => (
                    <div key={property.id} className="group flex gap-4 items-center p-5 hover:bg-bg-secondary/30 transition-colors">
                      <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-bg-secondary shrink-0 border border-border/60 shadow-sm">
                        {property.primary_image_url ? (
                          <img src={property.primary_image_url} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
                        ) : (
                          <Building2 className="h-6 w-6 text-text-tertiary m-auto absolute inset-0" />
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <h4 className="font-bold text-base text-text truncate group-hover:text-primary transition-colors">
                          <Link to={`/property/${property.id}`} className="focus:outline-none before:absolute before:inset-0">
                            {property.name}
                          </Link>
                        </h4>
                        <span className="text-xs text-text-secondary block font-medium mt-1 flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {property.city}, {property.state}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

        </div>

        {/* System Alerts */}
        <section>
          <h2 className="text-xl font-bold tracking-tight text-text mb-4">System Alerts</h2>
          <div className="bg-white rounded-2xl border border-border/60 shadow-sm overflow-hidden">
            <div className="divide-y divide-border/40">
              <div className="flex gap-5 p-6 hover:bg-bg-secondary/30 transition-colors">
                <div className="h-10 w-10 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shrink-0 shadow-sm border border-primary/20">
                  <Clock className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <Link to="/dashboard/holds" className="text-sm font-bold text-text hover:text-primary transition-colors block">
                    Check Reservation Status
                  </Link>
                  <span className="text-text-secondary text-xs block leading-relaxed max-w-2xl">
                    Verify hold request expiration timers and approval messages. Keep track of your deadlines to avoid losing your spot.
                  </span>
                </div>
              </div>

              <div className="flex gap-5 p-6 hover:bg-bg-secondary/30 transition-colors">
                <div className="h-10 w-10 rounded-2xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center shrink-0 shadow-sm border border-emerald-500/20">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <Link to="/notifications" className="text-sm font-bold text-text hover:text-primary transition-colors block">
                    Recent Activity Log
                  </Link>
                  <span className="text-text-secondary text-xs block leading-relaxed max-w-2xl">
                    View direct system notifications regarding check-in dates and changes to your accommodation.
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
