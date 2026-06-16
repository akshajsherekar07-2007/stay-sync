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
      <header className="sticky top-0 z-sticky w-full navbar-glass border-b border-border">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Branding */}
          <Link to="/" className="flex items-center gap-2 font-sans text-xl font-bold tracking-tight text-primary">
            <Home className="h-6 w-6" aria-hidden="true" />
            <span>StaySync</span>
          </Link>

          {/* Desktop Navigation */}
          {isDesktop ? (
            <nav className="flex items-center gap-6">
              <Link
                to="/properties"
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  location.pathname.startsWith("/properties") ? "text-primary" : "text-text-secondary"
                }`}
              >
                Browse Properties
              </Link>
              {isAuthenticated && (
                <Link
                  to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}
                  className={`text-sm font-medium transition-colors hover:text-primary ${
                    location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/owner/dashboard") ? "text-primary" : "text-text-secondary"
                  }`}
                >
                  Dashboard
                </Link>
              )}
              <div className="flex items-center gap-4 border-l border-border pl-6">
                {isAuthenticated && <NotificationBell />}
                <ThemeToggle />
                {isAuthenticated ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                        <Avatar size="sm">
                          <AvatarImage src={user?.profile?.avatar_url || undefined} alt={user?.profile?.full_name || "User avatar"} />
                          <AvatarFallback>{initials}</AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <div className="flex flex-col space-y-1 p-2">
                        <p className="text-sm font-medium leading-none">{user?.profile?.full_name || "My Account"}</p>
                        <p className="text-xs leading-none text-text-secondary">{user?.email}</p>
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"} className="flex items-center w-full">
                          <LayoutDashboard className="mr-2 h-4 w-4" aria-hidden="true" />
                          <span>Dashboard</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleLogout} className="text-danger focus:bg-danger/10 focus:text-danger cursor-pointer">
                        <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
                        <span>Log Out</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" asChild>
                      <Link to="/login">Log In</Link>
                    </Button>
                    <Button variant="default" asChild>
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
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle Navigation Menu"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
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
      <footer className="border-t border-border bg-bg-secondary py-8 text-center text-sm text-text-secondary">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p>© {new Date().getFullYear()} StaySync. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
