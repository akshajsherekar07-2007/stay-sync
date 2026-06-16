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

        {/* Protected Dashboard Routes */}
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
          </Route>
        </Route>

        {/* Fallback Route */}
        <Route path="*" element={<PlaceholderNotFound />} />
      </Route>
    </Routes>
  );
}

// ── Temporary Placeholders ──────────────────────────────────────────

function PlaceholderNotFound() {
  return (
    <div className="mx-auto max-w-md py-20 text-center px-4">
      <h1 className="text-7xl font-extrabold text-primary">404</h1>
      <h2 className="mt-4 text-2xl font-bold text-text">Page not found</h2>
      <p className="mt-2 text-text-secondary">
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
      </p>
      <div className="mt-8">
        <Button asChild>
          <Link to="/">Go back home</Link>
        </Button>
      </div>
    </div>
  );
}
