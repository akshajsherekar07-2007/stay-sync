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
import styles from "./RootLayout.module.css";

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

  const isPropertiesActive = location.pathname.startsWith("/properties");
  const isDashboardActive = location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/owner/dashboard");

  return (
    <div className={styles.layout}>
      {/* Responsive Header */}
      <header className={styles.header}>
        <div className={styles.headerContainer}>
          {/* Branding */}
          <Link to="/" className={styles.brand}>
            <div className={styles.brandIconWrapper}>
              <Home className={styles.brandIcon} aria-hidden="true" />
            </div>
            <span className={styles.brandText}>Stay</span><span className={styles.brandTextPrimary}>Sync</span>
          </Link>

          {/* Desktop Navigation */}
          {isDesktop ? (
            <nav className={styles.desktopNav}>
              <Link
                to="/properties"
                className={`${styles.navLink} ${isPropertiesActive ? styles.navLinkActive : ""}`}
              >
                Browse Properties
                <span className={styles.navLinkIndicator}></span>
              </Link>
              {isAuthenticated && (
                <Link
                  to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}
                  className={`${styles.navLink} ${isDashboardActive ? styles.navLinkActive : ""}`}
                >
                  Dashboard
                  <span className={styles.navLinkIndicator}></span>
                </Link>
              )}
              <div className={styles.navActions}>
                {isAuthenticated && <NotificationBell />}
                <ThemeToggle />
                {isAuthenticated ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className={styles.userAvatarBtn}>
                        <Avatar size="sm">
                          <AvatarImage src={user?.profile?.avatar_url || undefined} alt={user?.profile?.full_name || "User avatar"} />
                          <AvatarFallback className={styles.avatarFallback}>{initials}</AvatarFallback>
                        </Avatar>
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className={styles.dropdownMenu}>
                      <div className={styles.dropdownHeader}>
                        <p className={styles.dropdownName}>{user?.profile?.full_name || "My Account"}</p>
                        <p className={styles.dropdownEmail}>{user?.email}</p>
                      </div>
                      <DropdownMenuSeparator className={styles.dropdownSeparator} />
                      <DropdownMenuItem asChild className={styles.dropdownItem}>
                        <Link to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}>
                          <LayoutDashboard className={`${styles.dropdownIcon} ${styles.dropdownIconPrimary}`} aria-hidden="true" />
                          <span>Dashboard</span>
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className={styles.dropdownSeparator} />
                      <DropdownMenuItem onClick={handleLogout} className={`${styles.dropdownItem} ${styles.dropdownItemDanger}`}>
                        <LogOut className={styles.dropdownIcon} aria-hidden="true" />
                        <span>Log Out</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <div className={styles.authButtons}>
                    <Button variant="ghost" className={styles.loginBtn} asChild>
                      <Link to="/login">Log In</Link>
                    </Button>
                    <Button variant="default" className={styles.registerBtn} asChild>
                      <Link to="/register">Register</Link>
                    </Button>
                  </div>
                )}
              </div>
            </nav>
          ) : (
            // Mobile Hamburger Button
            <div className={styles.mobileActions}>
              {isAuthenticated && <NotificationBell />}
              <ThemeToggle />
              <button
                className={styles.mobileMenuBtn}
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle Navigation Menu"
              >
                {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      {!isDesktop && mobileMenuOpen && (
        <div className={styles.mobileDrawer}>
          <nav className={styles.mobileNav}>
            <Link
              to="/properties"
              className={`${styles.mobileNavLink} ${isPropertiesActive ? styles.mobileNavLinkActive : ""}`}
            >
              <Search className={styles.mobileNavIcon} aria-hidden="true" />
              <span>Browse Properties</span>
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to={user?.role === "owner" ? "/owner/dashboard" : "/dashboard"}
                  className={`${styles.mobileNavLink} ${isDashboardActive ? styles.mobileNavLinkActive : ""}`}
                >
                  <LayoutDashboard className={styles.mobileNavIcon} aria-hidden="true" />
                  <span>Dashboard</span>
                </Link>
                <div className={styles.mobileDivider} />
                <button
                  onClick={handleLogout}
                  className={styles.mobileLogout}
                >
                  <LogOut className={styles.mobileNavIcon} aria-hidden="true" />
                  <span>Log Out</span>
                </button>
              </>
            ) : (
              <>
                <div className={styles.mobileDivider} />
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
      <main className={styles.main}>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContainer}>
          <div className={styles.footerGrid}>
            {/* Brand Column */}
            <div className={styles.footerBrandCol}>
              <Link to="/" className={styles.footerBrand}>
                <div className={styles.footerBrandIcon}>
                  <Home aria-hidden="true" />
                </div>
                StaySync
              </Link>
              <p className={styles.footerDesc}>
                Connecting students with verified, high-quality accommodations. Hold beds in real-time and move in with confidence.
              </p>
            </div>

            {/* Quick Links */}
            <div className={styles.footerNavCol}>
              <h4 className={styles.footerNavTitle}>Platform</h4>
              <nav className={styles.footerNav}>
                <Link to="/properties" className={styles.footerNavLink}>Browse Properties</Link>
                <Link to="/register" className={styles.footerNavLink}>Create Account</Link>
                <Link to="/login" className={styles.footerNavLink}>Sign In</Link>
              </nav>
            </div>

            {/* Legal */}
            <div className={styles.footerNavCol}>
              <h4 className={styles.footerNavTitle}>Company</h4>
              <nav className={styles.footerNav}>
                <span className={styles.footerNavLink}>Privacy Policy</span>
                <span className={styles.footerNavLink}>Terms of Service</span>
                <span className={styles.footerNavLink}>Contact Support</span>
              </nav>
            </div>
          </div>

          <div className={styles.footerBottom}>
            <p className={styles.footerCopyright}>© {new Date().getFullYear()} StaySync. All rights reserved.</p>
            <p className={styles.footerCopyright}>Built for students, by students.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
