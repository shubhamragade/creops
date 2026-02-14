"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner"; // Kept for logic but used less visually
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/dashboard/MetricCard";
import {
    Users,
    Calendar,
    MessageSquare,
    ClipboardList,
    Package,
    AlertTriangle,
    ArrowRight,
    Plus,
    Activity,
    LogOut,
    TrendingUp,
    CheckCircle2
} from "lucide-react";
import Link from "next/link";
import { useToast } from "@/components/ui/toast-context";

interface DashboardData {
    bookings: {
        today_count: number;
        upcoming_24h: number;
        completed_this_week: number;
        no_show_this_week: number;
    };
    inbox: {
        total_conversations: number;
        unanswered_count: number;
        paused_conversations: number;
    };
    forms: {
        pending_count: number;
        overdue_count: number;
    };
    inventory: {
        id: number;
        name: string;
        quantity_available: number;
        low_threshold: number;
    }[];
    attention: {
        type: string;
        priority: string;
        message: string;
        action_type: string;
        entity_id: number | null;
    }[];
    recent_activity: {
        id: string;
        action: string;
        timestamp: string;
        actor_name: string;
        entity_type: string;
        entity_id: number | null;
        details: any;
    }[];
}

export default function DashboardPage() {
    const router = useRouter();
    const { showToast } = useToast();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const role = localStorage.getItem("user_role");
        const token = localStorage.getItem("access_token");

        if (!token) {
            router.replace("/login");
            return;
        }

        if (role === "staff") {
            router.replace("/staff");
            return;
        }

        api.get("/api/dashboard")
            .then((res) => setData(res.data))
            .catch((err) => {
                console.error("Dashboard fetch error:", err);
                setError("Failed to load dashboard data. Please try refreshing.");
                showToast("Failed to connect to server", "error");
            })
            .finally(() => setLoading(false));
    }, [router, showToast]);

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-center min-h-[400px]">
                <div className="bg-red-50 p-4 rounded-full mb-4">
                    <AlertTriangle className="h-8 w-8 text-red-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">Unable to Load Dashboard</h2>
                <p className="text-gray-500 max-w-md mt-2 mb-6">{error}</p>
                <Button onClick={() => window.location.reload()}>
                    Retry Connection
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-10">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-gray-900">Overview</h1>
                    <p className="text-sm text-gray-500">
                        {loading ? <Skeleton className="h-4 w-48" /> :
                            new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <Link href="/bookings?new=true">
                        <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm" disabled={loading}>
                            <Plus className="mr-2 h-4 w-4" /> New Booking
                        </Button>
                    </Link>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                    title="Bookings Today"
                    value={data?.bookings.today_count}
                    subtext={`${data?.bookings.upcoming_24h ?? 0} upcoming in 24h`}
                    icon={Calendar}
                    trend="neutral"
                    href="/bookings"
                    loading={loading}
                />
                <MetricCard
                    title="Unanswered Messages"
                    value={data?.inbox.unanswered_count}
                    subtext="Requires attention"
                    icon={MessageSquare}
                    trend={data?.inbox.unanswered_count && data.inbox.unanswered_count > 0 ? "negative" : "positive"}
                    href="/inbox"
                    loading={loading}
                />
                <MetricCard
                    title="Pending Forms"
                    value={data?.forms.pending_count}
                    subtext={`${data?.forms.overdue_count ?? 0} overdue`}
                    icon={ClipboardList}
                    trend={data?.forms.overdue_count && data.forms.overdue_count > 0 ? "negative" : "neutral"}
                    href="/bookings" // Assuming forms are linked to bookings
                    loading={loading}
                />
                <MetricCard
                    title="Low Inventory"
                    value={data?.inventory.length}
                    subtext="Items below threshold"
                    icon={Package}
                    trend={data?.inventory.length && data.inventory.length > 0 ? "negative" : "positive"}
                    href="/inventory"
                    loading={loading}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content Area (2/3) */}
                <div className="lg:col-span-2 space-y-8">

                    {/* Attention Section */}
                    {loading ? (
                        <Skeleton className="h-32 w-full rounded-xl" />
                    ) : (
                        data?.attention && data.attention.length > 0 && (
                            <Card className="border-l-4 border-l-amber-500 shadow-sm overflow-hidden">
                                <CardHeader className="bg-amber-50/50 pb-3">
                                    <CardTitle className="text-base font-semibold text-amber-900 flex items-center gap-2">
                                        <AlertTriangle className="h-4 w-4" /> Action Required
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-4 space-y-3">
                                    {data.attention.map((item, idx) => (
                                        <div key={idx} className="flex items-start justify-between gap-4 p-3 rounded-md bg-white border border-amber-100 hover:border-amber-200 transition-colors">
                                            <div className="flex gap-3">
                                                <div className={`mt-0.5 w-2 h-2 rounded-full ${item.priority === 'high' ? 'bg-red-500' : 'bg-amber-500'}`} />
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">{item.message}</p>
                                                    <p className="text-xs text-gray-500 capitalize">{item.type.replace('_', ' ')} • {item.priority} Priority</p>
                                                </div>
                                            </div>
                                            <Button size="sm" variant="outline" className="h-8 text-xs whitespace-nowrap" onClick={() => {
                                                if (item.action_type === 'RETRY_EMAIL') router.push('/bookings');
                                                else router.push('/dashboard');
                                            }}>
                                                Review
                                            </Button>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        )
                    )}

                    {/* Quick Stats / Secondary Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-gray-500">Weekly Performance</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {loading ? (
                                    <div className="space-y-4">
                                        <Skeleton className="h-4 w-full" />
                                        <Skeleton className="h-4 w-full" />
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-gray-600">Completed Bookings</span>
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold">{data?.bookings.completed_this_week}</span>
                                                <CheckCircle2 className="h-3 w-3 text-green-500" />
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-gray-600">No Shows</span>
                                            <span className={`font-semibold ${data?.bookings.no_show_this_week && data.bookings.no_show_this_week > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                                                {data?.bookings.no_show_this_week}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-gray-500">Quick Actions</CardTitle>
                            </CardHeader>
                            <CardContent className="grid grid-cols-2 gap-2">
                                <Link href="/staff-management" className="contents">
                                    <Button variant="outline" className="h-auto py-3 flex flex-col gap-1 items-center justify-center text-xs hover:border-indigo-200 hover:bg-indigo-50 transition-colors">
                                        <Users className="h-4 w-4 text-indigo-600" />
                                        <span>Invite Staff</span>
                                    </Button>
                                </Link>
                                <Link href="/inventory" className="contents">
                                    <Button variant="outline" className="h-auto py-3 flex flex-col gap-1 items-center justify-center text-xs hover:border-indigo-200 hover:bg-indigo-50 transition-colors">
                                        <Package className="h-4 w-4 text-indigo-600" />
                                        <span>Restock</span>
                                    </Button>
                                </Link>
                            </CardContent>
                        </Card>
                    </div>

                </div>

                {/* Sidebar Column (1/3) */}
                <div className="space-y-6">
                    {/* Activity Feed */}
                    <Card className="h-full flex flex-col">
                        <CardHeader className="pb-3 border-b border-gray-50">
                            <CardTitle className="text-sm font-medium text-gray-900 flex items-center gap-2">
                                <Activity className="h-4 w-4 text-gray-500" /> Recent Activity
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-auto max-h-[500px] pt-4 pr-2">
                            {loading ? (
                                <div className="space-y-4">
                                    <Skeleton className="h-12 w-full" />
                                    <Skeleton className="h-12 w-full" />
                                    <Skeleton className="h-12 w-full" />
                                </div>
                            ) : data?.recent_activity && data.recent_activity.length > 0 ? (
                                <div className="space-y-0">
                                    {data.recent_activity.map((activity, idx) => (
                                        <div key={activity.id} className="relative pl-6 pb-6 last:pb-0">
                                            {/* Timeline Line */}
                                            {idx !== data.recent_activity.length - 1 && (
                                                <div className="absolute left-[9px] top-2 bottom-0 w-px bg-gray-100" />
                                            )}

                                            {/* Dot */}
                                            <div className={`absolute left-0 top-1.5 h-4.5 w-4.5 rounded-full border-2 border-white shadow-sm flex items-center justify-center z-10 ${activity.entity_type === 'booking' ? 'bg-indigo-100' :
                                                    activity.entity_type === 'inventory' ? 'bg-orange-100' :
                                                        'bg-gray-100'
                                                }`}>
                                                <div className={`h-1.5 w-1.5 rounded-full ${activity.entity_type === 'booking' ? 'bg-indigo-600' :
                                                        activity.entity_type === 'inventory' ? 'bg-orange-500' :
                                                            'bg-gray-500'
                                                    }`} />
                                            </div>

                                            <div>
                                                <p className="text-sm text-gray-900 leading-snug">{activity.action}</p>
                                                <p className="text-xs text-gray-500 mt-0.5">
                                                    <span className="font-medium text-gray-700">{activity.actor_name}</span> • {formatTimeAgo(activity.timestamp)}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-gray-400 text-sm">
                                    No recent activity
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

function formatTimeAgo(timestamp: string) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return date.toLocaleDateString();
}
