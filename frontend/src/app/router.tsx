import { Routes, Route } from "react-router-dom";

/**
 * Application router — all route definitions live here.
 * Pages are imported lazily in future tasks for code splitting.
 */
export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<PlaceholderHome />} />
      <Route path="*" element={<PlaceholderNotFound />} />
    </Routes>
  );
}

/** Temporary placeholder — replaced in Phase 1.7 */
function PlaceholderHome() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-[var(--color-primary)]">StaySync</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">
          Live Accommodation Hold-Management Platform
        </p>
        <p className="mt-4 text-sm text-[var(--color-text-secondary)]">
          Phase 1.1 — Project Setup Complete ✓
        </p>
      </div>
    </div>
  );
}

function PlaceholderNotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-[var(--color-text-secondary)]">404</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">Page not found</p>
      </div>
    </div>
  );
}
