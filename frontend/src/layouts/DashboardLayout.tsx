import * as React from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { Menu, X, LayoutDashboard, Building2, Heart, LogOut, ChevronLeft, ChevronRight, Compass, Clock } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useAuth } from "../features/auth/hooks/useAuth";
import { Button } from "../components/ui/Button";
import { useMediaQuery } from "../hooks/useMediaQuery";
import styles from "./DashboardLayout.module.css";

export function DashboardLayout() {
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false);

  React.useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const isOwner = user?.role === "owner";

  const menuItems = isOwner
    ? [
        { label: "Overview", to: "/owner/dashboard", icon: LayoutDashboard },
        { label: "Hold Approvals", to: "/owner/holds", icon: Clock },
        { label: "My Properties", to: "/owner/properties", icon: Building2 },
      ]
    : [
        { label: "Overview", to: "/dashboard", icon: LayoutDashboard },
        { label: "Browse", to: "/properties", icon: Compass },
        { label: "My Holds", to: "/dashboard/holds", icon: Clock },
        { label: "Saved Properties", to: "/saved-properties", icon: Heart },
      ];

  return (
    <div className={styles.container}>
      {/* Sidebar - Desktop */}
      {isDesktop && (
        <aside
          className={`${styles.desktopSidebar} ${collapsed ? styles.desktopSidebarCollapsed : styles.desktopSidebarExpanded}`}
        >
          {/* Collapsible toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={styles.collapseBtn}
            aria-label={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {collapsed ? <ChevronRight className={styles.collapseIcon} /> : <ChevronLeft className={styles.collapseIcon} />}
          </button>

          {/* Branding / Header */}
          <div className={styles.sidebarHeader}>
            <Link to="/" className={styles.brandLink}>
              <div className={styles.brandIconWrapper}>
                <Building2 className={styles.brandIcon} aria-hidden="true" />
              </div>
              {!collapsed && <span className={styles.brandText}>StaySync</span>}
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className={styles.nav}>
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`${styles.navItem} ${active ? styles.navItemActive : styles.navItemInactive}`}
                >
                  <Icon className={styles.navIcon} aria-hidden="true" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Footer / Logout */}
          <div className={styles.sidebarFooter}>
            <button
              onClick={handleLogout}
              className={styles.logoutBtn}
            >
              <LogOut className={styles.navIcon} aria-hidden="true" />
              {!collapsed && <span>Log Out</span>}
            </button>
          </div>
        </aside>
      )}

      {/* Mobile Menu Trigger & Header */}
      {!isDesktop && (
        <div className={styles.mobileHeader}>
          <Link to="/" className={styles.mobileBrand}>
            <Building2 size={24} aria-hidden="true" />
            <span>StaySync</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            aria-label="Toggle Navigation Menu"
          >
            {mobileSidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </Button>
        </div>
      )}

      {/* Mobile Drawer */}
      {!isDesktop && mobileSidebarOpen && (
        <div className={styles.mobileMenuContainer}>
          {/* Backdrop */}
          <div className={styles.mobileBackdrop} onClick={() => setMobileSidebarOpen(false)} aria-hidden="true" />
          {/* Sidebar content */}
          <aside className={styles.mobileSidebar}>
            <div className={styles.mobileSidebarHeader}>
              <span className={styles.mobileSidebarTitle}>Menu</span>
              <Button variant="ghost" size="icon" onClick={() => setMobileSidebarOpen(false)}>
                <X size={20} />
              </Button>
            </div>
            <nav className={styles.mobileNav}>
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`${styles.mobileNavItem} ${active ? styles.mobileNavItemActive : styles.mobileNavItemInactive}`}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
            <div className={styles.mobileSidebarFooter}>
              <button
                onClick={handleLogout}
                className={styles.mobileLogoutBtn}
              >
                <LogOut size={20} aria-hidden="true" />
                <span>Log Out</span>
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Content Area */}
      <div className={styles.mainContent}>
        <main className={`${styles.mainWrapper} ${!isDesktop ? styles.mainWrapperMobilePadding : ""}`}>
          <div className={styles.mainInner}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
