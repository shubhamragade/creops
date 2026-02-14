"use client";

import { useState, useEffect, Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import {
    Calendar,
    Clock,
    User,
    CheckCircle,
    ArrowRight,
    ArrowLeft,
    MapPin,
    AlertCircle
} from "lucide-react";

function RescheduleContent() {
    const params = useParams();
    const searchParams = useSearchParams();
    const bookingId = searchParams.get("booking");
    const token = searchParams.get("token");

    const [booking, setBooking] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [selectedDate, setSelectedDate] = useState<string>("");
    const [selectedTime, setSelectedTime] = useState<string>("");
    const [availableSlots, setAvailableSlots] = useState<string[]>([]);
    const [slotsLoading, setSlotsLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (bookingId && token) {
            fetchBooking();
        } else {
            setError("Missing booking information. Please use the link from your email.");
            setLoading(false);
        }
    }, [bookingId, token]);

    useEffect(() => {
        if (booking && selectedDate) {
            fetchSlots();
        }
    }, [selectedDate, booking]);

    const fetchBooking = async () => {
        try {
            const res = await api.get(`/api/public/bookings/${bookingId}`, {
                params: { token }
            });
            setBooking(res.data);

            // Set default date to current booking date if in future
            const bookingDate = res.data.start_time.split('T')[0];
            const today = new Date().toISOString().split('T')[0];
            if (bookingDate >= today) {
                setSelectedDate(bookingDate);
            }
        } catch (err: any) {
            console.error("Failed to load booking", err);
            setError(err.response?.data?.detail || "Could not find your booking. It might have been cancelled or expired.");
        } finally {
            setLoading(false);
        }
    };

    const fetchSlots = async () => {
        if (!booking || !selectedDate) return;

        setSlotsLoading(true);
        setAvailableSlots([]);
        setSelectedTime("");

        try {
            const res = await api.get(`/api/public/services/${booking.service_id}/availability`, {
                params: { date: selectedDate }
            });
            setAvailableSlots(res.data);
        } catch (error) {
            console.error("Failed to load slots", error);
        } finally {
            setSlotsLoading(false);
        }
    };

    const handleReschedule = async () => {
        if (!selectedDate || !selectedTime) return;

        setSubmitting(true);
        setError("");

        try {
            const start_datetime = new Date(`${selectedDate}T${selectedTime}:00`).toISOString();

            await api.post(`/api/bookings/${bookingId}/reschedule`, {
                start_datetime: start_datetime
            }, {
                params: { token }
            });

            setSuccess(true);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Rescheduling failed. Slot might be taken.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50">
                <Spinner className="h-8 w-8 text-indigo-600" />
            </div>
        );
    }

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <Card className="max-w-md w-full text-center p-6 shadow-xl border-green-100">
                    <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
                        <CheckCircle className="h-10 w-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Appointment Rescheduled!</h2>
                    <p className="text-gray-500 mb-8">
                        Your appointment has been successfully moved. You will receive a new confirmation email shortly.
                    </p>

                    <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left space-y-2 border">
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Service</span>
                            <span className="text-sm font-medium">{booking?.service_name}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">New Date</span>
                            <span className="text-sm font-medium">{new Date(selectedDate).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">New Time</span>
                            <span className="text-sm font-medium">{selectedTime}</span>
                        </div>
                    </div>

                    <Button
                        onClick={() => window.close()}
                        variant="outline"
                        className="w-full"
                    >
                        Close Window
                    </Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                    {/* Header */}
                    <div className="p-6 border-b bg-white">
                        <h1 className="text-2xl font-bold text-gray-900">Reschedule Appointment</h1>
                        <p className="text-gray-500 text-sm mt-1">
                            Current: <span className="font-medium text-gray-700">{booking?.service_name} on {new Date(booking?.start_time).toLocaleString()}</span>
                        </p>
                    </div>

                    {/* Content Body */}
                    <div className="p-6">
                        {error && (
                            <div className="mb-6 p-4 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100 flex items-start gap-3">
                                <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                                <div>
                                    <span className="font-bold">Error:</span> {error}
                                </div>
                            </div>
                        )}

                        {!error && (
                            <div className="space-y-8">
                                <div className="grid md:grid-cols-2 gap-8">
                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-3">1. Select New Date</label>
                                        <input
                                            type="date"
                                            required
                                            min={new Date().toISOString().split("T")[0]}
                                            value={selectedDate}
                                            onChange={(e) => setSelectedDate(e.target.value)}
                                            className="w-full p-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium text-lg"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-semibold text-gray-700 mb-3">
                                            2. Choose New Time
                                        </label>

                                        {slotsLoading ? (
                                            <div className="flex items-center justify-center h-48 border-2 border-dashed rounded-xl">
                                                <Spinner className="h-6 w-6 text-indigo-600" />
                                            </div>
                                        ) : !selectedDate ? (
                                            <div className="flex items-center justify-center h-48 border-2 border-dashed rounded-xl text-gray-400 bg-gray-50 text-sm">
                                                Select a date first
                                            </div>
                                        ) : availableSlots.length === 0 ? (
                                            <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed rounded-xl text-gray-500 bg-gray-50 p-4 text-center">
                                                <Calendar className="h-8 w-8 text-gray-300 mb-2" />
                                                <p className="text-sm">No availability on this day.</p>
                                                <p className="text-xs text-gray-400 mt-1">Please try another date.</p>
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                                                {availableSlots.map(time => (
                                                    <button
                                                        key={time}
                                                        onClick={() => setSelectedTime(time)}
                                                        className={`
                                                            py-3 px-4 text-sm font-semibold rounded-xl transition-all
                                                            ${selectedTime === time
                                                                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-200 transform scale-[1.02]"
                                                                : "bg-white border-2 border-gray-100 text-gray-700 hover:border-indigo-200 hover:bg-gray-50"}
                                                        `}
                                                    >
                                                        {time}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {selectedTime && (
                                    <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center gap-4 text-indigo-800 animate-in fade-in slide-in-from-bottom-2">
                                        <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center shadow-sm">
                                            <CheckCircle className="h-6 w-6 text-indigo-600" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium opacity-80 uppercase tracking-wider">New Appointment Time</p>
                                            <p className="text-lg font-bold">
                                                {new Date(selectedDate).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })} at {selectedTime}
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer / Navigation */}
                    <div className="p-6 border-t bg-gray-50 flex justify-end">
                        <Button
                            onClick={handleReschedule}
                            disabled={submitting || !selectedTime || !selectedDate || !!error}
                            size="lg"
                            className="bg-indigo-600 hover:bg-indigo-700 text-white min-w-[200px] h-14 rounded-xl text-lg font-bold"
                        >
                            {submitting ? (
                                <><Spinner className="mr-3 h-5 w-5" /> Updating...</>
                            ) : (
                                <>Confirm Change <ArrowRight className="ml-3 h-5 w-5" /></>
                            )}
                        </Button>
                    </div>
                </div>

                <p className="text-center text-gray-400 text-sm mt-8">
                    Powered by <span className="font-semibold">CareOps</span> &bull; 100% Secure
                </p>
            </div>
        </div>
    );
}

export default function ReschedulePage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center bg-gray-50 text-indigo-600">Loading rescheduling options...</div>}>
            <RescheduleContent />
        </Suspense>
    );
}
