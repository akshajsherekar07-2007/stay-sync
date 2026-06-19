import * as React from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { Menu, X, LayoutDashboard, Building2, Heart, LogOut, ChevronLeft, ChevronRight, Compass, Clock } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useAuth } from "../features/auth/hooks/useAuth";
import { Button } from "../components/ui/Button";
import { useMediaQuery } from "../hooks/useMediaQuery";

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
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-text">
      {/* Sidebar - Desktop */}
      {isDesktop && (
        <aside
          className={`relative flex flex-col border-r border-white/[0.06] bg-sidebar-bg transition-all duration-300 ${
            collapsed ? "w-16" : "w-64"
          }`}
        >
          {/* Collapsible toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="absolute -right-3 top-6 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-bg shadow-sm hover:bg-bg-secondary cursor-pointer z-10"
            aria-label={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>

          {/* Branding / Header */}
          <div className="flex h-16 items-center px-4 font-sans font-bold tracking-tight text-white border-b border-white/[0.06]">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/20">
                <Building2 className="h-4 w-4 shrink-0 text-white" aria-hidden="true" />
              </div>
              {!collapsed && <span className="text-lg">StaySync</span>}
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 space-y-1 p-3 mt-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                    active
                      ? "bg-sidebar-active-bg text-sidebar-active shadow-sm"
                      : "text-sidebar-text/70 hover:bg-sidebar-hover hover:text-sidebar-text"
                  }`}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Footer / Logout */}
          <div className="border-t border-white/[0.06] p-3">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-rose-400/80 hover:bg-rose-500/10 hover:text-rose-400 transition-all duration-200 cursor-pointer"
            >
              <LogOut className="h-5 w-5 shrink-0" aria-hidden="true" />
              {!collapsed && <span>Log Out</span>}
            </button>
          </div>
        </aside>
      )}

      {/* Mobile Menu Trigger & Header */}
      {!isDesktop && (
        <div className="fixed top-0 left-0 right-0 z-sticky flex h-16 items-center justify-between border-b border-border bg-bg-secondary px-4">
          <Link to="/" className="flex items-center gap-2 font-sans font-bold text-primary">
            <Building2 className="h-6 w-6" aria-hidden="true" />
            <span>StaySync</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            aria-label="Toggle Navigation Menu"
          >
            {mobileSidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </Button>
        </div>
      )}

      {/* Mobile Drawer */}
      {!isDesktop && mobileSidebarOpen && (
        <div className="fixed inset-0 z-overlay flex">
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileSidebarOpen(false)} aria-hidden="true" />
          {/* Sidebar content */}
          <aside className="relative flex w-64 flex-col bg-bg-secondary border-r border-border h-full p-4 space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <span className="font-bold text-primary text-lg">Menu</span>
              <Button variant="ghost" size="icon" onClick={() => setMobileSidebarOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="flex-1 space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      active
                        ? "bg-primary text-white shadow-sm"
                        : "text-text-secondary hover:bg-bg-tertiary hover:text-text"
                    }`}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="border-t border-border/50 pt-4">
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-danger hover:bg-danger/10 transition-colors cursor-pointer"
              >
                <LogOut className="h-5 w-5" aria-hidden="true" />
                <span>Log Out</span>
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className={`flex-1 overflow-y-auto p-4 md:p-6 ${!isDesktop ? "pt-20" : ""}`}>
          <div className="mx-auto max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
