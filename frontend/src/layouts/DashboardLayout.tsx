import * as React from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { Menu, X, LayoutDashboard, Building2, Heart, LogOut, ChevronLeft, ChevronRight, Compass, Clock } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useAuth } from "../features/auth/hooks/useAuth";
import { Button } from "../components/ui/Button";
import { Avatar, AvatarImage, AvatarFallback } from "../components/ui/Avatar";
import { ThemeToggle } from "../components/common/ThemeToggle";
import { NotificationBell } from "../components/layout/NotificationBell";
import { Logo } from "../components/common/Logo";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "../components/ui/DropdownMenu";
import { useMediaQuery } from "../hooks/useMediaQuery";

export function DashboardLayout() {
  const { user, isAuthenticated } = useAuthStore();
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

  const initials = user?.profile?.full_name
    ? user.profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() || "U";

  return (
    <div className="flex h-screen w-full overflow-hidden bg-bg text-text">
      {/* Sidebar - Desktop */}
      {isDesktop && (
        <aside
          className={`relative flex flex-col border-r border-border bg-bg-secondary transition-all duration-300 ease-in-out ${
            collapsed ? "w-16" : "w-64"
          }`}
        >
          {/* Logo Section */}
          <div className="flex h-16 items-center px-4 border-b border-border/50">
            {collapsed ? (
              <Building2 className="h-8 w-8 text-primary mx-auto shrink-0" />
            ) : (
              <Logo />
            )}
          </div>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-bg shadow-sm cursor-pointer z-10 hover:bg-bg-secondary transition-colors"
            aria-label={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>

          {/* Navigation Links */}
          <nav className="flex-1 flex flex-col gap-1 p-3 mt-2 overflow-y-auto">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                    active 
                      ? "bg-primary text-white shadow-sm" 
                      : "text-text-secondary hover:bg-border/30 hover:text-text"
                  }`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>
        </aside>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-bg px-4 sm:px-6 z-10 shadow-sm">
          {/* Left side */}
          <div className="flex items-center gap-4">
            {!isDesktop ? (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMobileSidebarOpen(true)}
                  aria-label="Open Navigation Menu"
                  className="mr-2"
                >
                  <Menu size={24} />
                </Button>
                <Logo />
              </>
            ) : (
               <div className="text-sm font-semibold text-text-secondary hidden sm:block">
                 {isOwner ? "Owner Dashboard" : "Student Portal"}
               </div>
            )}
          </div>

          {/* Right side: Actions & Profile */}
          <div className="flex items-center gap-3 sm:gap-4">
            {isAuthenticated && <NotificationBell />}
            <ThemeToggle />
            
            {isAuthenticated && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center justify-center rounded-full ring-2 ring-transparent hover:ring-primary/20 focus:outline-none focus:ring-primary/50 transition-all">
                    <Avatar size="sm" className="border border-border/50">
                      <AvatarImage src={user?.profile?.avatar_url || undefined} alt={user?.profile?.full_name || "User"} />
                      <AvatarFallback className="bg-primary/10 text-primary font-bold">
                        {initials}
                      </AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 mt-2">
                  <div className="flex flex-col px-4 py-3">
                    <p className="text-sm font-bold text-text truncate">
                      {user?.profile?.full_name || "My Account"}
                    </p>
                    <p className="text-xs text-text-secondary truncate mt-0.5">
                      {user?.email}
                    </p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-danger focus:text-danger focus:bg-danger/10 cursor-pointer py-2.5">
                    <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
                    <span className="font-medium">Log Out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </header>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto bg-bg p-4 sm:p-6 lg:p-8">
          <div className="mx-auto w-full max-w-full">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Drawer Overlay */}
      {!isDesktop && mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
            onClick={() => setMobileSidebarOpen(false)} 
            aria-hidden="true" 
          />
          
          {/* Sidebar */}
          <aside className="relative flex w-64 flex-col bg-bg-secondary shadow-xl transition-transform duration-300 transform translate-x-0">
            <div className="flex h-16 items-center justify-between border-b border-border/50 px-4">
              <Logo />
              <Button variant="ghost" size="icon" onClick={() => setMobileSidebarOpen(false)}>
                <X size={20} />
              </Button>
            </div>
            
            <nav className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                      active 
                        ? "bg-primary text-white shadow-sm" 
                        : "text-text-secondary hover:bg-border/30 hover:text-text"
                    }`}
                  >
                    <Icon size={20} aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
            
            <div className="border-t border-border/50 p-4">
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-danger hover:bg-danger/10 transition-colors"
              >
                <LogOut size={20} aria-hidden="true" />
                <span>Log Out</span>
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
