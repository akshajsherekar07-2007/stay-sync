import * as React from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { Menu, X, Home, Search, LayoutDashboard, LogOut } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useAuth } from "../features/auth/hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Avatar, AvatarImage, AvatarFallback } from "../components/ui/Avatar";
import { ThemeToggle } from "../components/common/ThemeToggle";
import { NotificationBell } from "../components/layout/NotificationBell";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "../components/ui/DropdownMenu";
import { useMediaQuery } from "../hooks/useMediaQuery";

export function RootLayout() {
  const { isAuthenticated, user } = useAuthStore();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  React.useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const initials = user?.profile?.full_name
    ? user.profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() || "U";

  return (
    <div className="flex min-h-screen flex-col bg-bg text-text">
      {/* Responsive Header */}
      <header className="sticky top-0 z-sticky w-full bg-bg/80 backdrop-blur-xl border-b border-border/40 shadow-sm transition-all duration-300">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Branding */}
          <Link to="/" className="flex items-center gap-2 font-sans text-xl font-bold tracking-tight text-primary group">
            <div className="bg-primary/10 p-1.5 rounded-lg group-hover:bg-primary/20 transition-colors">
              <Home className="h-5 w-5 text-primary" aria-hidden="true" />
            </div>
            <span className="text-text">Stay</span><span className="text-primary -ml-1">Sync</span>
          </Link>

          {/* Desktop Navigation */}
          {isDesktop ? (
            <nav className="flex items-center gap-8">
              <Link
                to="/properties"
                className={`text-sm font-semibold transition-all duration-300 hover:text-primary relative group ${
                  location.pathname.startsWith("/properties") ? "text-primary" : "text-text-secondary"
                }`}
              >
                Browse Properties
                <span className={`absolute -bottom-1.5 left-0 h-0.5 bg-primary transition-all duration-300 ${
                  location.pathname.startsWith("/properties") ? "w-full" : "w-0 group-hover:w-full"
                }`}></span>
              </Link>
              {isAuthenticated && (
                <Link
                  to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}
                  className={`text-sm font-semibold transition-all duration-300 hover:text-primary relative group ${
                    location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/owner/dashboard") ? "text-primary" : "text-text-secondary"
                  }`}
                >
                  Dashboard
                  <span className={`absolute -bottom-1.5 left-0 h-0.5 bg-primary transition-all duration-300 ${
                    location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/owner/dashboard") ? "w-full" : "w-0 group-hover:w-full"
                  }`}></span>
                </Link>
              )}
              <div className="flex items-center gap-4 border-l border-border/40 pl-6 ml-2">
                {isAuthenticated && <NotificationBell />}
                <ThemeToggle />
                {isAuthenticated ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="relative h-10 w-10 rounded-full hover:ring-2 hover:ring-primary/20 transition-all duration-300">
                        <Avatar size="sm">
                          <AvatarImage src={user?.profile?.avatar_url || undefined} alt={user?.profile?.full_name || "User avatar"} />
                          <AvatarFallback className="font-bold bg-primary/10 text-primary">{initials}</AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56 rounded-xl border border-border/50 shadow-lg p-1.5">
                      <div className="flex flex-col space-y-1 p-2.5">
                        <p className="text-sm font-bold leading-none">{user?.profile?.full_name || "My Account"}</p>
                        <p className="text-xs leading-none text-text-secondary mt-1">{user?.email}</p>
                      </div>
                      <DropdownMenuSeparator className="bg-border/40" />
                      <DropdownMenuItem asChild className="rounded-lg cursor-pointer font-medium hover:bg-bg-secondary focus:bg-bg-secondary p-2.5 my-0.5">
                        <Link to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"} className="flex items-center w-full">
                          <LayoutDashboard className="mr-2 h-4 w-4 text-primary" aria-hidden="true" />
                          <span>Dashboard</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="bg-border/40" />
                      <DropdownMenuItem onClick={handleLogout} className="rounded-lg text-danger font-medium hover:bg-danger/10 focus:bg-danger/10 focus:text-danger cursor-pointer p-2.5 my-0.5 transition-colors">
                        <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
                        <span>Log Out</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <div className="flex items-center gap-3">
                    <Button variant="ghost" className="font-bold" asChild>
                      <Link to="/login">Log In</Link>
                    </Button>
                    <Button variant="default" className="font-bold shadow-[0_4px_14px_0_rgba(13,148,136,0.39)] hover:shadow-[0_6px_20px_rgba(13,148,136,0.23)]" asChild>
                      <Link to="/register">Register</Link>
                    </Button>
                  </div>
                )}
              </div>
            </nav>
          ) : (
            // Mobile Hamburger Button
            <div className="flex items-center gap-4">
              {isAuthenticated && <NotificationBell />}
              <ThemeToggle />
              <Button
                variant="ghost"
                size="icon"
                className="hover:bg-bg-secondary active:scale-95 transition-all"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle Navigation Menu"
              >
                {mobileMenuOpen ? <X className="h-6 w-6 text-text" /> : <Menu className="h-6 w-6 text-text" />}
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      {!isDesktop && mobileMenuOpen && (
        <div className="fixed inset-0 top-16 z-sticky w-full bg-bg/95 backdrop-blur-md transition-all duration-300 md:hidden border-b border-border">
          <nav className="flex flex-col space-y-4 p-6">
            <Link
              to="/properties"
              className={`flex items-center gap-2 text-lg font-medium ${
                location.pathname.startsWith("/properties") ? "text-primary" : "text-text-secondary"
              }`}
            >
              <Search className="h-5 w-5" aria-hidden="true" />
              <span>Browse Properties</span>
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}
                  className={`flex items-center gap-2 text-lg font-medium ${
                    location.pathname === "/dashboard" || location.pathname === "/owner/dashboard" ? "text-primary" : "text-text-secondary"
                  }`}
                >
                  <LayoutDashboard className="h-5 w-5" aria-hidden="true" />
                  <span>Dashboard</span>
                </Link>
                <div className="h-px bg-border my-2" />
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 text-left text-lg font-medium text-danger"
                >
                  <LogOut className="h-5 w-5" aria-hidden="true" />
                  <span>Log Out</span>
                </button>
              </>
            ) : (
              <>
                <div className="h-px bg-border my-2" />
                <Button variant="outline" asChild className="w-full justify-center">
                  <Link to="/login">Log In</Link>
                </Button>
                <Button variant="default" asChild className="w-full justify-center">
                  <Link to="/register">Register</Link>
                </Button>
              </>
            )}
          </nav>
        </div>
      )}

      {/* Page Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-sidebar-bg text-sidebar-text">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Brand Column */}
            <div className="space-y-4">
              <Link to="/" className="flex items-center gap-2.5 font-bold text-white text-lg">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/20">
                  <Home className="h-4 w-4 text-white" />
                </div>
                StaySync
              </Link>
              <p className="text-sm text-sidebar-text/60 leading-relaxed max-w-xs">
                Connecting students with verified, high-quality accommodations. Hold beds in real-time and move in with confidence.
              </p>
            </div>

            {/* Quick Links */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-sidebar-text/40">Platform</h4>
              <nav className="flex flex-col space-y-3">
                <Link to="/properties" className="text-sm text-sidebar-text/70 hover:text-white transition-colors">Browse Properties</Link>
                <Link to="/register" className="text-sm text-sidebar-text/70 hover:text-white transition-colors">Create Account</Link>
                <Link to="/login" className="text-sm text-sidebar-text/70 hover:text-white transition-colors">Sign In</Link>
              </nav>
            </div>

            {/* Legal */}
            <div className="space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-sidebar-text/40">Company</h4>
              <nav className="flex flex-col space-y-3">
                <span className="text-sm text-sidebar-text/70">Privacy Policy</span>
                <span className="text-sm text-sidebar-text/70">Terms of Service</span>
                <span className="text-sm text-sidebar-text/70">Contact Support</span>
              </nav>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-white/[0.06] flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-xs text-sidebar-text/40">© {new Date().getFullYear()} StaySync. All rights reserved.</p>
            <p className="text-xs text-sidebar-text/40">Built for students, by students.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
