import React, { useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard,
  Building2,
  FileText,
  Briefcase,
  GitMerge,
  AlertOctagon,
  BarChart3,
  Bell,
  Users,
  Settings,
  ChevronDown,
  LogOut,
  Menu,
  X,
  Shield,
  ClipboardList,
  Clock,
  BookOpen,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { getUnreadCount } from "@/api/notifications";

// ── Nav config ────────────────────────────────────────────────────────────────

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  requiredRoles?: string[];
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: "Main",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "Institutions",
    items: [
      { label: "Institution Directory", href: "/institutions", icon: Building2 },
    ],
  },
  {
    title: "Complaints & Cases",
    items: [
      { label: "Complaints", href: "/complaints", icon: FileText },
      { label: "Cases", href: "/cases", icon: Briefcase },
    ],
  },
  {
    title: "Coordination",
    items: [
      { label: "Overlap Alerts", href: "/overlaps", icon: GitMerge },
      { label: "Conflict Warnings", href: "/conflicts", icon: AlertOctagon },
    ],
  },
  {
    title: "Analytics",
    items: [
      { label: "Reports", href: "/reports", icon: BarChart3 },
      { label: "Notifications", href: "/notifications", icon: Bell },
      { label: "Documentation", href: "/docs.html", icon: BookOpen },
    ],
  },
  {
    title: "Administration",
    items: [
      { label: "User Management", href: "/admin/users", icon: Users, requiredRoles: ["admin", "system_administrator"] },
      { label: "Bureau Config", href: "/admin/bureaus", icon: Settings, requiredRoles: ["admin", "system_administrator"] },
      { label: "SLA Settings", href: "/admin/sla", icon: Clock, requiredRoles: ["admin", "system_administrator"] },
      { label: "Audit Log", href: "/admin/audit", icon: ClipboardList, requiredRoles: ["admin", "system_administrator"] },
    ],
  },
];

// ── Breadcrumb ────────────────────────────────────────────────────────────────

function useBreadcrumbs() {
  const location = useLocation();
  const parts = location.pathname.split("/").filter(Boolean);

  const crumbs = parts.map((part, i) => {
    const path = "/" + parts.slice(0, i + 1).join("/");
    const label = part
      .replace(/-/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    return { label, path };
  });

  return [{ label: "Home", path: "/" }, ...crumbs];
}

function Breadcrumbs() {
  const crumbs = useBreadcrumbs();

  return (
    <nav className="flex items-center gap-1 text-sm text-gray-500" aria-label="Breadcrumb">
      {crumbs.map((crumb, i) => (
        <React.Fragment key={crumb.path}>
          {i > 0 && <span className="text-gray-300">/</span>}
          {i === crumbs.length - 1 ? (
            <span className="text-gray-700 font-medium">{crumb.label}</span>
          ) : (
            <NavLink to={crumb.path} className="hover:text-indigo-600 transition-colors">
              {crumb.label}
            </NavLink>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

// ── Sidebar NavItem ───────────────────────────────────────────────────────────

function SidebarNavItem({
  item,
  onClick,
}: {
  item: NavItem;
  onClick?: () => void;
}) {
  const { hasRole } = useAuth();

  if (item.requiredRoles && !hasRole(...item.requiredRoles)) {
    return null;
  }

  return (
    <NavLink
      to={item.href}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
          isActive
            ? "bg-indigo-900 text-white font-medium"
            : "text-blue-100 hover:bg-indigo-900/60 hover:text-white"
        )
      }
    >
      <item.icon className="h-4 w-4 shrink-0" />
      {item.label}
    </NavLink>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function Sidebar({ onClose }: { onClose?: () => void }) {
  return (
    <div className="flex h-full flex-col" style={{ backgroundColor: "#3f51b5" }}>
      {/* AICTE Brand Header */}
      <div className="flex items-center gap-2 px-3 py-3 border-b border-indigo-400/40">
        <img
          src="/logo.png"
          alt="AICTE Logo"
          className="h-10 w-10 object-contain shrink-0"
        />
        <div className="min-w-0 flex-1">
          <div
            className="text-white font-bold leading-tight truncate"
            style={{ fontSize: "0.72rem", fontFamily: "'Noto Sans Devanagari', sans-serif" }}
          >
            अखिल भारतीय तकनीकी शिक्षा परिषद्
          </div>
          <div className="text-blue-200 leading-tight" style={{ fontSize: "0.6rem" }}>
            All India Council for Technical Education
          </div>
        </div>
        {onClose && (
          <button
            className="ml-auto text-blue-200 hover:text-white lg:hidden shrink-0"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
      {/* Saffron accent line */}
      <div className="h-0.5" style={{ background: "linear-gradient(to right, #ff9800, #f44336, #ff9800)" }} />

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navSections.map((section) => (
          <div key={section.title}>
            <p className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider text-blue-300">{section.title}</p>
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <SidebarNavItem key={item.href} item={item} onClick={onClose} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-indigo-400/40 p-3">
        <div className="flex items-center gap-2 px-3 py-2">
          <Shield className="h-4 w-4 text-blue-300" />
          <span className="text-xs text-blue-300">Secure Portal</span>
        </div>
      </div>
    </div>
  );
}

// ── Main layout ───────────────────────────────────────────────────────────────

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: getUnreadCount,
    refetchInterval: 60_000,
  });

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-shrink-0 lg:flex-col">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-64 flex flex-col">
            <Sidebar onClose={() => setMobileMenuOpen(false)} />
          </div>
        </div>
      )}

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b border-gray-200 bg-white px-4 shadow-sm">
          {/* Mobile menu button */}
          <button
            className="text-gray-500 hover:text-gray-700 lg:hidden"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          {/* Breadcrumb */}
          <div className="flex-1 hidden sm:block">
            <Breadcrumbs />
          </div>

          {/* Right side */}
          <div className="ml-auto flex items-center gap-3">
            {/* Notifications */}
            <button
              className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              onClick={() => navigate("/notifications")}
              title="Notifications"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <Badge
                  variant="destructive"
                  className="absolute -right-1 -top-1 h-5 min-w-[1.25rem] px-1 text-[10px] flex items-center justify-center"
                >
                  {unreadCount > 99 ? "99+" : unreadCount}
                </Badge>
              )}
            </button>

            {/* User menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 rounded-full pr-2 pl-1 py-1 hover:bg-gray-100 transition-colors">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                  </Avatar>
                  <span className="hidden md:block text-sm font-medium text-gray-700 max-w-[140px] truncate">
                    {user?.full_name}
                  </span>
                  <ChevronDown className="h-4 w-4 text-gray-400 hidden md:block" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="font-medium">{user?.full_name}</div>
                  <div className="text-xs text-gray-400 font-normal">{user?.email}</div>
                  <div className="text-xs text-indigo-600 font-normal mt-0.5">{user?.role?.replace(/_/g, " ")}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                  <LayoutDashboard className="mr-2 h-4 w-4" />
                  Dashboard
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/notifications")}>
                  <Bell className="mr-2 h-4 w-4" />
                  Notifications
                  {unreadCount > 0 && (
                    <span className="ml-auto text-xs bg-red-100 text-red-700 rounded-full px-1.5">
                      {unreadCount}
                    </span>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-red-600 focus:text-red-600 focus:bg-red-50">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
