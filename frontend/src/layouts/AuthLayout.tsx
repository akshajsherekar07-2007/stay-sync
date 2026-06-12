import { Link, Navigate, Outlet } from "react-router-dom";
import { Home } from "lucide-react";
import { useAuthStore } from "../stores/authStore";

export function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen w-full bg-bg text-text md:grid md:grid-cols-2">
      {/* Decorative Left Panel (Desktop only) */}
      <div className="hidden flex-col justify-between bg-primary p-12 text-white md:flex">
        <div className="flex items-center gap-2 text-2xl font-bold tracking-tight">
          <Home className="h-8 w-8" aria-hidden="true" />
          <span>StaySync</span>
        </div>
        <div className="space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight leading-tight lg:text-5xl">
            Find the perfect student accommodation, instantly.
          </h1>
          <p className="text-lg text-primary-light">
            StaySync connects students with premium accommodation options. Manage bookings, holds, and properties all in one secure place.
          </p>
        </div>
        <div className="text-sm text-primary-light/80">
          © {new Date().getFullYear()} StaySync. Trusted by thousands of students.
        </div>
      </div>

      {/* Right Panel (Form content) */}
      <div className="flex w-full items-center justify-center p-6 sm:p-12 md:p-16">
        <div className="mx-auto flex w-full max-w-md flex-col justify-center space-y-6">
          {/* Mobile Branding */}
          <div className="flex flex-col items-center gap-2 md:hidden">
            <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-primary">
              <Home className="h-8 w-8" aria-hidden="true" />
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
