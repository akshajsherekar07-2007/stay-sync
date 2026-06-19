import { Link, Navigate, Outlet } from "react-router-dom";
import { Building2 } from "lucide-react";
import { useAuthStore } from "../stores/authStore";

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen w-full bg-bg text-text md:grid md:grid-cols-2 overflow-hidden">
      {/* Decorative Left Panel (Desktop only) */}
      <div className="relative hidden flex-col justify-between bg-sidebar-bg p-12 text-sidebar-text md:flex overflow-hidden">
        {/* Subtle Background Pattern */}
        <div 
          className="absolute inset-0 opacity-[0.03]" 
          style={{ 
            backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`, 
            backgroundSize: `32px 32px` 
          }}
        />
        
        {/* Soft glowing orb in the background */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[140px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

        <div className="relative z-10 flex items-center gap-3 text-3xl font-extrabold tracking-tight text-white">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-xl shadow-primary/30">
            <Building2 className="h-6 w-6 text-white" aria-hidden="true" />
          </div>
          <span>StaySync</span>
        </div>

        {/* Abstract Product Mockup */}
        <div className="relative z-10 flex flex-col items-center justify-center flex-1 my-12">
          <div className="w-full max-w-[420px] rounded-3xl bg-white/[0.03] border border-white/10 p-8 backdrop-blur-md shadow-2xl overflow-hidden animate-slide-up" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center gap-3 mb-8">
              <div className="flex gap-2">
                <div className="h-3 w-3 rounded-full bg-white/20" />
                <div className="h-3 w-3 rounded-full bg-white/20" />
                <div className="h-3 w-3 rounded-full bg-white/20" />
              </div>
            </div>
            <div className="space-y-5">
              <div className="h-8 w-3/4 rounded-lg bg-white/10" />
              <div className="space-y-3">
                <div className="h-4 w-full rounded bg-white/5" />
                <div className="h-4 w-5/6 rounded bg-white/5" />
                <div className="h-4 w-4/6 rounded bg-white/5" />
              </div>
              <div className="flex gap-4 pt-6">
                <div className="h-24 flex-1 rounded-2xl bg-primary/20 border border-primary/30" />
                <div className="h-24 flex-1 rounded-2xl bg-white/5" />
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 space-y-6 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <blockquote className="text-xl font-medium leading-relaxed tracking-tight text-white">
            "StaySync has completely transformed how we manage our properties. 
            The waitlist features and instant holds fill our beds 40% faster than before."
          </blockquote>
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-lg font-bold text-white">
              S
            </div>
            <div>
              <p className="font-semibold text-white">Sarah Jenkins</p>
              <p className="text-sm text-sidebar-text/70">Property Manager at Apex Housing</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel (Form content) */}
      <div className="relative flex w-full items-center justify-center p-6 sm:p-12 md:p-16 bg-bg z-10">
        <div className="mx-auto flex w-full max-w-[400px] flex-col justify-center space-y-8 animate-fade-in">
          {/* Mobile Branding */}
          <div className="flex flex-col items-center gap-2 md:hidden mb-4">
            <Link to="/" className="flex items-center gap-2.5 text-2xl font-bold text-text">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary shadow-md">
                <Building2 className="h-5 w-5 text-white" aria-hidden="true" />
              </div>
              <span>StaySync</span>
            </Link>
          </div>
          {/* Routed components (Login / Register form) */}
          <Outlet />
        </div>
      </div>
    </div>
  );
}
