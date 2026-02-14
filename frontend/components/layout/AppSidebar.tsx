"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Calendar,
    MessageSquare,
    Package,
    Users,
    Settings,
    Zap,
    LogOut,
    Home,
    FileText
} from "lucide-react";
import { cn } from "@/lib/utils";

import React from "react";

interface AppSidebarProps {
    role: "owner" | "staff" | null;
}

export function AppSidebar({ role }: AppSidebarProps) {
    const pathname = usePathname();
    const [permissions, setPermissions] = React.useState<Record<string, boolean>>({});

    React.useEffect(() => {
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('user_permissions');
            if (stored) {
                try {
                    // Handle both stringified JSON and direct string access if needed
                    // Backend returns dict/json, so stored string should be parsable
                    const parsed = JSON.parse(stored);
                    // Handle if parsed is a string (double encoded)
                    setPermissions(typeof parsed === 'string' ? JSON.parse(parsed) : parsed);
                } catch (e) {
                    console.error("Failed to parse permissions", e);
                }
            }
        }
    }, []);

    const ownerItems = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "Inbox", href: "/inbox", icon: MessageSquare },
        { name: "Bookings", href: "/bookings", icon: Calendar },
        { name: "Services", href: "/services", icon: Zap }, // Using Zap icon for Services
        { name: "Leads", href: "/leads", icon: Users },
        { name: "Customers", href: "/contacts", icon: Users },
        { name: "Inventory", href: "/inventory", icon: Package },
        { name: "Forms", href: "/forms-manage", icon: FileText },
        { name: "Automations", href: "/automations", icon: Zap },
        { name: "Team", href: "/staff-management", icon: Users },
        { name: "Settings", href: "/dashboard/settings", icon: Settings },
    ];

    const staffItemsRaw = [
        { name: "My Dashboard", href: "/staff", icon: Home, key: "dashboard" }, // Always shown
        { name: "Inbox", href: "/inbox", icon: MessageSquare, key: "inbox" },
        { name: "Bookings", href: "/bookings", icon: Calendar, key: "bookings" },
        { name: "Leads", href: "/leads", icon: Users, key: "leads" },
        { name: "Customers", href: "/contacts", icon: Users, key: "leads" }, // Grouped with leads
        { name: "Inventory", href: "/inventory", icon: Package, key: "inventory" },
    ];

    // Filter staff items based on permissions
    const staffItems = staffItemsRaw.filter(item => {
        if (item.key === "dashboard") return true; // Dashboard always access
        return permissions[item.key] === true;
    });

    const items = role === "staff" ? staffItems : ownerItems;

    return (
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
            <div className="p-6 border-b border-gray-200">
                <h1 className="text-xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
                    CareOps
                    {role === "staff" && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
                            STAFF
                        </span>
                    )}
                </h1>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {items.map((item) => {
                    const Icon = item.icon;
                    // Active state logic: partial match for sub-routes
                    const isActive = pathname === item.href || (pathname?.startsWith(item.href + "/") && item.href !== "/");

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-gray-100 text-gray-900 shadow-sm"
                                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                            )}
                        >
                            <Icon className={cn("h-4 w-4", isActive ? "text-gray-900" : "text-gray-400")} />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-gray-200">
                <button
                    onClick={() => {
                        localStorage.removeItem("access_token");
                        localStorage.removeItem("user_role");
                        window.location.href = "/login";
                    }}
                    className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 w-full transition-colors"
                >
                    <LogOut className="h-4 w-4" />
                    Sign out
                </button>
            </div>
        </div>
    );
}
