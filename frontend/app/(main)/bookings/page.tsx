"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast-context";
import {
    Calendar,
    Clock,
    User,
    ArrowLeft,
    CheckCircle2,
    XCircle,
    MoreHorizontal,
    RefreshCcw,
    AlertCircle,
    CalendarDays
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function BookingsPage() {
    const router = useRouter();
    const { showToast } = useToast();
    const [bookings, setBookings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [role, setRole] = useState<string>("");

    // Detail State
    const [selectedBooking, setSelectedBooking] = useState<any | null>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    useEffect(() => {
        const userRole = localStorage.getItem("user_role");
        setRole(userRole || "");
        fetchBookings();
    }, []);

    const fetchBookings = async () => {
        try {
            const res = await api.get("/api/bookings");
            const sorted = res.data.sort((a: any, b: any) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());
            setBookings(sorted);
        } catch (err) {
            console.error(err);
            showToast("Failed to load bookings", "error");
        } finally {
            setLoading(false);
        }
    };

    const fetchHistory = async (bookingId: number) => {
        setHistoryLoading(true);
        try {
            const res = await api.get(`/api/bookings/${bookingId}/history`);
            setHistory(res.data);
        } catch (err) {
            console.error(err);
            showToast("Failed to load history", "error");
        } finally {
            setHistoryLoading(false);
        }
    };

    const handleSelectBooking = (booking: any) => {
        if (selectedBooking?.id === booking.id) {
            setSelectedBooking(null); // Toggle off
        } else {
            setSelectedBooking(booking);
            fetchHistory(booking.id);
        }
    };

    const handleAction = async (action: string, id: number, extra: any = {}) => {
        if (!confirm(`Are you sure you want to ${action}?`)) return;

        try {
            if (action === 'cancel') {
                await api.post(`/api/bookings/${id}/cancel`);
            } else if (action === 'restore') {
                await api.post(`/api/bookings/${id}/restore`);
            } else if (action === 'retry_comm') {
                await api.post(`/api/communications/${extra.comm_id}/retry`);
            } else if (action === 'reschedule') {
                const newDate = prompt("Enter new datetime (YYYY-MM-DD HH:MM):");
                if (!newDate) return;
                await api.patch(`/api/bookings/${id}`, { start_datetime: new Date(newDate).toISOString() });
            }

            showToast(`${action.replace('_', ' ')} successful`, "success");
            fetchBookings();
            if (selectedBooking && selectedBooking.id === id) {
                // Refresh history too
                fetchHistory(id);
            }
        } catch (err: any) {
            console.error(err);
            const msg = err.response?.data?.detail || `Failed to ${action}`;
            showToast(msg, "error");
        }
    };

    const handleBack = () => {
        if (role === 'staff') {
            router.push('/staff');
        } else {
            router.push('/dashboard');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50/50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" onClick={handleBack} className="text-gray-500 hover:text-gray-900 -ml-2">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back
                        </Button>
                        <h1 className="text-xl font-bold text-gray-900 tracking-tight">Bookings</h1>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="text-sm text-gray-500">
                            {bookings.length} Total
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8 items-start">

                {/* List View */}
                <div className={cn(
                    "flex-1 transition-all duration-300",
                    selectedBooking ? "w-1/2" : "w-full"
                )}>
                    <Card className="shadow-sm border-gray-200 overflow-hidden">
                        <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 grid grid-cols-12 gap-4 text-xs font-medium text-gray-500 uppercase tracking-wider">
                            <div className="col-span-4">Service & Customer</div>
                            <div className="col-span-3">Date & Time</div>
                            <div className="col-span-3">Status</div>
                            <div className="col-span-2 text-right">Details</div>
                        </div>

                        <div className="divide-y divide-gray-100">
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <div key={i} className="px-4 py-4 grid grid-cols-12 gap-4 items-center">
                                        <div className="col-span-4 space-y-2">
                                            <Skeleton className="h-4 w-3/4" />
                                            <Skeleton className="h-3 w-1/2" />
                                        </div>
                                        <div className="col-span-3">
                                            <Skeleton className="h-4 w-full" />
                                        </div>
                                        <div className="col-span-3">
                                            <Skeleton className="h-6 w-16 rounded-full" />
                                        </div>
                                        <div className="col-span-2 flex justify-end">
                                            <Skeleton className="h-8 w-16" />
                                        </div>
                                    </div>
                                ))
                            ) : bookings.length === 0 ? (
                                <div className="p-8">
                                    <EmptyState
                                        icon={CalendarDays}
                                        title="No bookings found"
                                        description="You don't have any bookings yet. Create one to get started."
                                    />
                                </div>
                            ) : (
                                bookings.map((booking) => (
                                    <div
                                        key={booking.id}
                                        onClick={() => handleSelectBooking(booking)}
                                        className={cn(
                                            "px-4 py-4 grid grid-cols-12 gap-4 items-center cursor-pointer transition-colors hover:bg-gray-50",
                                            selectedBooking?.id === booking.id ? "bg-indigo-50/50" : ""
                                        )}
                                    >
                                        <div className="col-span-4">
                                            <div className="font-medium text-gray-900">{booking.service?.name || "Unknown Service"}</div>
                                            <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-0.5">
                                                <User className="w-3 h-3" />
                                                {booking.contact?.full_name || "Guest"}
                                            </div>
                                        </div>

                                        <div className="col-span-3">
                                            <div className="text-sm text-gray-700 flex flex-col">
                                                <span className="font-medium">{new Date(booking.start_time).toLocaleDateString()}</span>
                                                <span className="text-xs text-gray-500">{new Date(booking.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>

                                        <div className="col-span-3">
                                            <Badge variant={booking.status === 'confirmed' ? 'success' : booking.status === 'cancelled' ? 'destructive' : booking.status === 'pending' ? 'info' : 'secondary'}>
                                                {booking.status === 'pending' ? 'Scheduled' : booking.status}
                                            </Badge>
                                        </div>

                                        <div className="col-span-2 text-right">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className={cn(
                                                    "h-8 w-8 p-0 rounded-full",
                                                    selectedBooking?.id === booking.id ? "bg-indigo-100 text-indigo-700" : "text-gray-400 hover:text-gray-600"
                                                )}
                                            >
                                                <MoreHorizontal className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </Card>
                </div>

                {/* Detail Panel */}
                {selectedBooking && (
                    <div className="w-[400px] shrink-0 animate-in slide-in-from-right-10 duration-300">
                        <Card className="border-gray-200 shadow-md sticky top-24">
                            <CardHeader className="bg-gray-50 border-b border-gray-100 pb-4">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Booking #{selectedBooking.id}</CardTitle>
                                    <Button variant="ghost" size="sm" onClick={() => setSelectedBooking(null)} className="h-8 w-8 p-0 rounded-full">
                                        <XCircle className="w-5 h-5 text-gray-400" />
                                    </Button>
                                </div>
                                <CardDescription className="flex items-center gap-2 mt-1">
                                    <Badge variant="outline" className="bg-white">{selectedBooking.service?.name}</Badge>
                                    <span className="text-xs">•</span>
                                    <span className="text-xs">{new Date(selectedBooking.created_at).toLocaleDateString()}</span>
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="p-0">
                                {/* Customer Info */}
                                <div className="p-5 border-b border-gray-100">
                                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Customer</h4>
                                    <div className="flex items-start gap-3">
                                        <div className="h-10 w-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm">
                                            {selectedBooking.contact?.full_name?.substring(0, 2).toUpperCase() || "GU"}
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900">{selectedBooking.contact?.full_name}</p>
                                            <p className="text-xs text-gray-500">{selectedBooking.contact?.email}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Timeline */}
                                <div className="p-5">
                                    <div className="flex items-center justify-between mb-4">
                                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Activity Log</h4>
                                        <Button variant="ghost" size="sm" onClick={() => fetchHistory(selectedBooking.id)} className="h-6 w-6 p-0" disabled={historyLoading}>
                                            <RefreshCcw className={cn("w-3 h-3 text-gray-400", historyLoading && "animate-spin")} />
                                        </Button>
                                    </div>

                                    <div className="space-y-6 pl-2">
                                        {historyLoading ? (
                                            <div className="space-y-3">
                                                <Skeleton className="h-4 w-3/4" />
                                                <Skeleton className="h-4 w-1/2" />
                                            </div>
                                        ) : history.length === 0 ? (
                                            <p className="text-xs text-center text-gray-400 py-2">No activity recorded.</p>
                                        ) : (
                                            history.map((event, idx) => (
                                                <div key={event.id} className="relative pl-6 border-l border-gray-200 pb-1 last:pb-0 last:border-0">
                                                    <div className={cn(
                                                        "absolute left-[-5px] top-1.5 h-2.5 w-2.5 rounded-full border border-white ring-1 ring-gray-100",
                                                        event.type === 'audit' ? 'bg-indigo-500' : 'bg-orange-500'
                                                    )} />

                                                    <div className="text-xs mb-1 font-medium text-gray-900">{event.action}</div>
                                                    <div className="text-[10px] text-gray-400 mb-2">
                                                        {new Date(event.created_at).toLocaleString()}
                                                    </div>

                                                    {event.type === 'communication' && (
                                                        <div className="mt-2 bg-gray-50 border border-gray-200 rounded p-2 text-[10px] space-y-1">
                                                            <div className="flex justify-between">
                                                                <span className="text-gray-500">To:</span>
                                                                <span className="font-medium">{event.details.recipient}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-gray-500">Status:</span>
                                                                <Badge
                                                                    variant={event.details.status === 'failed' ? 'destructive' : 'success'}
                                                                    className="h-4 px-1 text-[8px] uppercase"
                                                                >
                                                                    {event.details.status}
                                                                </Badge>
                                                            </div>

                                                            {event.details.status === 'failed' && role === 'owner' && (
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="w-full mt-2 h-6 text-[10px]"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleAction('retry_comm', selectedBooking.id, { comm_id: event.id.split('_')[1] });
                                                                    }}
                                                                >
                                                                    <RefreshCcw className="w-3 h-3 mr-1" /> Retry
                                                                </Button>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>

                                {/* Actions Footer */}
                                <div className="p-4 bg-gray-50 border-t border-gray-100 flex gap-2">
                                    {selectedBooking.status === 'cancelled' ? (
                                        role === 'owner' ? (
                                            <Button size="sm" className="w-full bg-green-600 hover:bg-green-700 text-white" onClick={() => handleAction('restore', selectedBooking.id)}>
                                                <RefreshCcw className="w-3 h-3 mr-2" /> Restore Booking
                                            </Button>
                                        ) : (
                                            <div className="w-full p-2 bg-amber-50 text-amber-800 text-xs text-center rounded border border-amber-200">
                                                Cancelled. Contact owner to restore.
                                            </div>
                                        )
                                    ) : (
                                        <>
                                            <Button size="sm" variant="outline" className="flex-1" onClick={() => handleAction('reschedule', selectedBooking.id)}>
                                                Reschedule
                                            </Button>
                                            <Button size="sm" variant="destructive" className="flex-1" onClick={() => handleAction('cancel', selectedBooking.id)}>
                                                Cancel
                                            </Button>
                                        </>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
}
