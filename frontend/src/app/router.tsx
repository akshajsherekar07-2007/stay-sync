import { Routes, Route, Link } from "react-router-dom";
import { Heart, Building2 } from "lucide-react";
import { RootLayout } from "../layouts/RootLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { ProtectedRoute } from "../components/common/ProtectedRoute";
import { RoleRoute } from "../components/common/RoleRoute";
import { GuestRoute } from "../components/common/GuestRoute";
import { UserRole } from "../types/enums";
import { Button } from "../components/ui/Button";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        {/* Public Routes */}
        <Route path="/" element={<PlaceholderHome />} />
        <Route path="/properties" element={<PlaceholderProperties />} />
        <Route path="/property/:id" element={<PlaceholderPropertyView />} />

        {/* Guest Only Routes (Login/Register) */}
        <Route element={<GuestRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<PlaceholderLogin />} />
            <Route path="/register" element={<PlaceholderRegister />} />
          </Route>
        </Route>

        {/* Protected Dashboard Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            {/* Student-Only Routes */}
            <Route element={<RoleRoute allowedRoles={[UserRole.STUDENT]} />}>
              <Route path="/dashboard" element={<PlaceholderStudentDashboard />} />
              <Route path="/saved-properties" element={<PlaceholderSavedProperties />} />
            </Route>

            {/* Owner-Only Routes */}
            <Route element={<RoleRoute allowedRoles={[UserRole.OWNER]} />}>
              <Route path="/owner/dashboard" element={<PlaceholderOwnerDashboard />} />
              <Route path="/owner/properties" element={<PlaceholderOwnerProperties />} />
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

function PlaceholderHome() {
  return (
    <div className="mx-auto max-w-4xl py-20 text-center px-4">
      <h1 className="text-5xl font-extrabold tracking-tight text-text sm:text-6xl">
        Welcome to <span className="text-primary">StaySync</span>
      </h1>
      <p className="mt-6 text-xl text-text-secondary">
        StaySync connects students with premium housing options. Discover, save, and hold accommodations instantly.
      </p>
      <div className="mt-10 flex justify-center gap-4">
        <Button variant="default" size="lg" asChild>
          <Link to="/properties">Browse Properties</Link>
        </Button>
        <Button variant="outline" size="lg" asChild>
          <Link to="/login">Student Portal</Link>
        </Button>
      </div>
    </div>
  );
}

function PlaceholderProperties() {
  return (
    <div className="mx-auto max-w-7xl py-12 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-extrabold tracking-tight text-text">Browse Accommodations</h1>
      <p className="mt-2 text-text-secondary">Find the best PG, flats, and hostels tailored for college students.</p>
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((id) => (
          <div key={id} className="rounded-lg border border-border p-6 shadow-sm hover:shadow-md transition-shadow bg-card">
            <h3 className="text-lg font-bold text-text">Accommodation Option #{id}</h3>
            <p className="mt-2 text-sm text-text-secondary">Premium shared double rooms located near top campuses.</p>
            <div className="mt-4 flex justify-between items-center">
              <span className="text-sm font-semibold text-primary">₹12,000 / month</span>
              <Button size="sm" variant="outline" asChild>
                <Link to={`/property/${id}`}>View Details</Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PlaceholderPropertyView() {
  return (
    <div className="mx-auto max-w-3xl py-12 px-4 sm:px-6">
      <div className="rounded-lg border border-border p-8 shadow-sm bg-card">
        <h1 className="text-3xl font-extrabold tracking-tight text-text font-sans">Accommodation Details</h1>
        <p className="mt-4 text-text-secondary">
          Detailed campus descriptions, occupancy rates, pricing brackets, and reservation timelines will be shown here.
        </p>
        <div className="mt-8">
          <Button variant="default" asChild>
            <Link to="/properties">Back to Listings</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function PlaceholderLogin() {
  return (
    <div className="rounded-lg border border-border bg-card p-8 shadow-md">
      <h2 className="text-2xl font-bold tracking-tight text-text">Sign in to your account</h2>
      <p className="mt-2 text-sm text-text-secondary">Enter your email and credentials below.</p>
      <div className="mt-6 space-y-4">
        <div className="rounded bg-bg-secondary p-4 text-xs text-text-secondary text-left space-y-1">
          <p><strong>Dev Quick Login:</strong></p>
          <p>• Student: student@example.com (pass: Password123)</p>
          <p>• Owner: owner@example.com (pass: Password123)</p>
        </div>
        <Button className="w-full" variant="default">Login (Mock Action)</Button>
        <p className="text-center text-sm text-text-secondary mt-4">
          Don't have an account?{" "}
          <Link to="/register" className="text-primary hover:underline font-semibold">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}

function PlaceholderRegister() {
  return (
    <div className="rounded-lg border border-border bg-card p-8 shadow-md">
      <h2 className="text-2xl font-bold tracking-tight text-text">Create an account</h2>
      <p className="mt-2 text-sm text-text-secondary">Register as a student looking for housing or an owner managing properties.</p>
      <div className="mt-6 space-y-4">
        <Button className="w-full" variant="default">Sign Up (Mock Action)</Button>
        <p className="text-center text-sm text-text-secondary mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:underline font-semibold">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}

function PlaceholderStudentDashboard() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-primary/10 p-6 border border-primary/20">
        <h1 className="text-2xl font-extrabold tracking-tight text-primary">Student Dashboard Overview</h1>
        <p className="mt-2 text-text-secondary text-sm">
          Welcome to your StaySync account. Track active reservations, holds, and browse local property listings.
        </p>
      </div>
      <div className="grid gap-6 sm:grid-cols-2">
        <div className="rounded-lg border border-border p-6 bg-card shadow-xs">
          <h3 className="font-bold text-text">Active Holds</h3>
          <p className="text-sm text-text-secondary mt-1">You currently have no active accommodation hold periods.</p>
        </div>
        <div className="rounded-lg border border-border p-6 bg-card shadow-xs">
          <h3 className="font-bold text-text">Quick Actions</h3>
          <div className="mt-4 flex gap-2">
            <Button size="sm" asChild>
              <Link to="/properties">Search Rooms</Link>
            </Button>
            <Button size="sm" variant="outline" asChild>
              <Link to="/saved-properties">View Wishlist</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function PlaceholderSavedProperties() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-text">Saved Properties</h1>
      <p className="text-text-secondary">A watchlist of accommodations you are interested in holding or booking.</p>
      <div className="rounded-lg border border-dashed border-border p-12 text-center bg-card">
        <Heart className="mx-auto h-12 w-12 text-text-tertiary" />
        <h3 className="mt-4 text-lg font-semibold text-text">Your wishlist is empty</h3>
        <p className="mt-2 text-sm text-text-secondary">Browse listings and click the save icon to add properties here.</p>
        <div className="mt-6">
          <Button asChild>
            <Link to="/properties">Browse Properties</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function PlaceholderOwnerDashboard() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-primary/10 p-6 border border-primary/20">
        <h1 className="text-2xl font-extrabold tracking-tight text-primary font-sans">Owner Dashboard Overview</h1>
        <p className="mt-2 text-text-secondary text-sm">
          Welcome, property manager. Monitor check-in rates, active bookings, and verify tenant details.
        </p>
      </div>
      <div className="grid gap-6 sm:grid-cols-3">
        <div className="rounded-lg border border-border p-4 bg-card shadow-xs">
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">My Properties</span>
          <div className="text-2xl font-bold text-text mt-1">0</div>
        </div>
        <div className="rounded-lg border border-border p-4 bg-card shadow-xs">
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Active Bookings</span>
          <div className="text-2xl font-bold text-text mt-1">0</div>
        </div>
        <div className="rounded-lg border border-border p-4 bg-card shadow-xs">
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Total Revenue</span>
          <div className="text-2xl font-bold text-text mt-1">₹0</div>
        </div>
      </div>
      <div className="rounded-lg border border-border p-6 bg-card">
        <h3 className="font-bold text-text">Quick Onboarding</h3>
        <p className="text-sm text-text-secondary mt-2">Get started by listing your hostel, PG, or student apartments.</p>
        <div className="mt-4">
          <Button asChild>
            <Link to="/owner/properties">Manage Properties</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function PlaceholderOwnerProperties() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-text font-sans">My Listed Properties</h1>
          <p className="text-text-secondary text-sm mt-1">Manage, update, and inspect your student accommodations.</p>
        </div>
        <Button variant="default">Add New Property</Button>
      </div>
      <div className="rounded-lg border border-dashed border-border p-12 text-center bg-card">
        <Building2 className="mx-auto h-12 w-12 text-text-tertiary" />
        <h3 className="mt-4 text-lg font-semibold text-text">No properties listed yet</h3>
        <p className="mt-2 text-sm text-text-secondary">Create a listing to reach students looking for PG or Flat stays.</p>
      </div>
    </div>
  );
}

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
