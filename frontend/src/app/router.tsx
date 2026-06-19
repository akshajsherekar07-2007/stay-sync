import { Routes, Route, Link } from "react-router-dom";
import { RootLayout } from "../layouts/RootLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { RoleRoute } from "../components/common/RoleRoute";
import { GuestRoute } from "../components/common/GuestRoute";
import { UserRole } from "../types/enums";
import { Button } from "../components/ui/Button";
import LoginPage from "../features/auth/pages/LoginPage";
import RegisterPage from "../features/auth/pages/RegisterPage";
import HomePage from "../features/home/pages/HomePage";
import BrowsePage from "../features/properties/pages/BrowsePage";
import PropertyDetailsPage from "../features/properties/pages/PropertyDetailsPage";
import StudentDashboard from "../features/dashboard/pages/StudentDashboard";
import SavedPropertiesPage from "../features/dashboard/pages/SavedPropertiesPage";
import OwnerDashboard from "../features/owner/pages/OwnerDashboard";
import ManagePropertiesPage from "../features/owner/pages/ManagePropertiesPage";
import CreatePropertyPage from "../features/owner/pages/CreatePropertyPage";
import EditPropertyPage from "../features/owner/pages/EditPropertyPage";
import StudentHoldsPage from "../features/dashboard/pages/StudentHoldsPage";
import OwnerHoldsPage from "../features/owner/pages/OwnerHoldsPage";
import NotificationPage from "../features/dashboard/pages/NotificationPage";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/properties" element={<BrowsePage />} />
        <Route path="/property/:id" element={<PropertyDetailsPage />} />

        {/* Guest Only Routes (Login/Register) */}
        <Route element={<GuestRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
        </Route>

        {/* Fallback Route for non-dashboard paths */}
        <Route path="*" element={<PlaceholderNotFound />} />
      </Route>

      {/* Protected Dashboard Routes - Independent of RootLayout */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          {/* Student-Only Routes */}
          <Route element={<RoleRoute allowedRoles={[UserRole.STUDENT]} />}>
            <Route path="/dashboard" element={<StudentDashboard />} />
            <Route path="/dashboard/holds" element={<StudentHoldsPage />} />
            <Route path="/saved-properties" element={<SavedPropertiesPage />} />
          </Route>

          {/* Owner-Only Routes */}
          <Route element={<RoleRoute allowedRoles={[UserRole.OWNER]} />}>
            <Route path="/owner/dashboard" element={<OwnerDashboard />} />
            <Route path="/owner/holds" element={<OwnerHoldsPage />} />
            <Route path="/owner/properties" element={<ManagePropertiesPage />} />
            <Route path="/owner/properties/create" element={<CreatePropertyPage />} />
            <Route path="/owner/properties/:id/edit" element={<EditPropertyPage />} />
          </Route>

          {/* Authenticated Routes (Both Roles) */}
          <Route element={<RoleRoute allowedRoles={[UserRole.STUDENT, UserRole.OWNER]} />}>
            <Route path="/notifications" element={<NotificationPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

// ── Temporary Placeholders ──────────────────────────────────────────

function PlaceholderNotFound() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-4 min-h-[60vh] animate-fade-in relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="text-center relative z-10 max-w-lg mx-auto">
        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-[2rem] bg-card shadow-sm ring-1 ring-border/40 mb-8 transform -rotate-6 hover:rotate-0 transition-transform duration-300">
          <span className="text-5xl font-black text-primary">404</span>
        </div>
        
        <h1 className="text-3xl font-extrabold text-text tracking-tight sm:text-4xl">Page not found</h1>
        <p className="mt-4 text-base text-text-secondary leading-relaxed">
          The property or page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
        </p>
        
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button asChild size="lg" className="w-full sm:w-auto font-bold rounded-xl shadow-[0_4px_14px_0_rgba(13,148,136,0.25)] hover:shadow-[0_6px_20px_rgba(13,148,136,0.23)] hover:-translate-y-0.5 transition-all">
            <Link to="/">Return Home</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full sm:w-auto font-bold rounded-xl bg-card border-none ring-1 ring-border/40 hover:bg-bg-secondary hover:-translate-y-0.5 transition-all">
            <Link to="/properties">Browse Properties</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
