"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { Calendar, MessageSquare, ClipboardList, CheckCircle2, Clock, MapPin, ArrowRight, User } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface StaffDashboardData {
    bookings_today: any[];
    inbox_unread: number;
}

export default function StaffDashboard() {
    const router = useRouter();
    const [data, setData] = useState<StaffDashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [permissions, setPermissions] = useState<Record<string, boolean>>({});

    useEffect(() => {
        // 1. Role Check
        const role = localStorage.getItem("user_role");
        const token = localStorage.getItem("access_token");

        if (!token) {
            router.replace("/login");
            return;
        }

        // Load permissions
        const storedPermissions = localStorage.getItem("user_permissions");
        let perms: Record<string, boolean> = {};
        if (storedPermissions) {
            try {
                const parsed = JSON.parse(storedPermissions);
                perms = typeof parsed === 'string' ? JSON.parse(parsed) : parsed;
                setPermissions(perms);
            } catch (e) {
                console.error("Failed to parse permissions", e);
            }
        }

        const fetchData = async () => {
            try {
                const promises = [];

                // Fetch bookings if allowed
                if (perms.bookings) {
                    promises.push(
                        api.get("/api/bookings")
                            .then(res => {
                                const today = new Date().toISOString().split('T')[0];
                                return res.data.filter((b: any) => b.start_time.startsWith(today));
                            })
                            .catch(() => [])
                    );
                } else {
                    promises.push(Promise.resolve([]));
                }

                // Fetch inbox status if allowed
                if (perms.inbox) {
                    promises.push(
                        api.get("/api/conversations")
                            .then(res => {
                                return res.data.filter((c: any) => !c.last_message_is_internal && c.is_paused === false).length;
                            })
                            .catch(() => 0)
                    );
                } else {
                    promises.push(Promise.resolve(0));
                }

                const [todaysBookings, unread] = await Promise.all(promises);

                setData({
                    bookings_today: todaysBookings,
                    inbox_unread: unread
                });
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [router]);

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-10">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-gray-900">Today's Work</h1>
                    <p className="text-sm text-gray-500">
                        {loading ? <Skeleton className="h-4 w-48" /> :
                            new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {permissions.bookings && (
                    <MetricCard
                        title="Scheduled Today"
                        value={data?.bookings_today?.length || 0}
                        subtext="Appointments"
                        icon={Calendar}
                        trend="neutral"
                        href="/bookings"
                        loading={loading}
                    />
                )}
                {permissions.inbox && (
                    <MetricCard
                        title="Unread Messages"
                        value={data?.inbox_unread || 0}
                        subtext="Requires attention"
                        icon={MessageSquare}
                        trend={data?.inbox_unread && data.inbox_unread > 0 ? "negative" : "positive"}
                        href="/inbox"
                        loading={loading}
                    />
                )}
            </div>

            <div className="grid gap-8 md:grid-cols-3">
                {/* PRIMARY COLUMN: Tasks/Bookings */}
                {permissions.bookings && (
                    <div className="md:col-span-2 space-y-6">
                        <Card className="shadow-sm border-gray-200">
                            <CardHeader className="border-b border-gray-100 bg-gray-50/50 py-4">
                                <CardTitle className="text-base font-medium flex items-center gap-2 text-gray-900">
                                    <Calendar className="h-4 w-4 text-indigo-600" /> Schedule
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-6">
                                {loading ? (
                                    <div className="space-y-4">
                                        <Skeleton className="h-24 w-full rounded-lg" />
                                        <Skeleton className="h-24 w-full rounded-lg" />
                                    </div>
                                ) : data?.bookings_today && data.bookings_today.length > 0 ? (
                                    <div className="space-y-4">
                                        {data.bookings_today.map((booking: any) => (
                                            <div key={booking.id} className="group relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg border border-gray-100 bg-white hover:border-indigo-200 hover:shadow-sm transition-all">
                                                <div className="flex gap-4 items-start">
                                                    <div className="flex flex-col items-center justify-center w-14 h-14 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-100">
                                                        <span className="text-lg leading-none">{new Date(booking.start_time).toLocaleTimeString([], { hour: '2-digit', hour12: false }).split(':')[0]}</span>
                                                        <span className="text-[10px] font-medium opacity-70 uppercase mt-0.5">{new Date(booking.start_time).toLocaleTimeString([], { minute: '2-digit' })}</span>
                                                    </div>
                                                    <div>
                                                        <h3 className="font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">{booking.service?.name}</h3>
                                                        <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                                                            <span className="flex items-center gap-1">
                                                                <User className="h-3.5 w-3.5" />
                                                                {booking.contact?.full_name || "Guest"}
                                                            </span>
                                                            {booking.contact?.phone && (
                                                                <span className="text-xs text-gray-400">• {booking.contact.phone}</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-3 pl-18 sm:pl-0">
                                                    <Badge
                                                        variant={booking.status === 'confirmed' ? 'success' : 'secondary'}
                                                        className="capitalize"
                                                    >
                                                        {booking.status}
                                                    </Badge>

                                                    <Link href={`/bookings`}>
                                                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-full text-gray-400 hover:text-indigo-600 hover:bg-indigo-50">
                                                            <ArrowRight className="h-4 w-4" />
                                                        </Button>
                                                    </Link>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-12 text-center text-gray-400 border border-dashed border-gray-200 rounded-lg bg-gray-50/30">
                                        <div className="h-12 w-12 bg-green-50 rounded-full flex items-center justify-center mb-3">
                                            <CheckCircle2 className="h-6 w-6 text-green-500" />
                                        </div>
                                        <p className="font-medium text-gray-900">All caught up!</p>
                                        <p className="text-sm mt-1">No bookings scheduled for the rest of the day.</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* SECONDARY COLUMN: Quick Access */}
                <div className="space-y-6">
                    <Card className="shadow-sm">
                        <CardHeader className="pb-3 border-b border-gray-50">
                            <CardTitle className="text-sm font-medium text-gray-500 uppercase tracking-wider">Quick Links</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-4 space-y-2">
                            {permissions.bookings && (
                                <Link href="/bookings" className="block">
                                    <Button variant="outline" className="w-full justify-start text-gray-700 hover:text-indigo-700 hover:border-indigo-200 hover:bg-indigo-50 transition-all h-10">
                                        <Calendar className="mr-3 h-4 w-4 text-gray-400" /> View Calendar
                                    </Button>
                                </Link>
                            )}
                            {permissions.inbox && (
                                <Link href="/inbox" className="block">
                                    <Button variant="outline" className="w-full justify-start text-gray-700 hover:text-indigo-700 hover:border-indigo-200 hover:bg-indigo-50 transition-all h-10">
                                        <MessageSquare className="mr-3 h-4 w-4 text-gray-400" /> Messages
                                    </Button>
                                </Link>
                            )}
                            {/* Fallback if no permissions */}
                            {!permissions.bookings && !permissions.inbox && (
                                <p className="text-sm text-gray-500 italic">No quick links available based on your permissions.</p>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
