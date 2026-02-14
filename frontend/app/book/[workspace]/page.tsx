"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import api from "../../../lib/api";
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
    ChevronRight
} from "lucide-react";

interface Service {
    id: number;
    name: string;
    duration_minutes: number;
    location: string;
    availability?: any;
}

export default function BookingPage({ params }: { params: { workspace: string } }) {
    const [services, setServices] = useState<Service[]>([]);
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState(1); // 1: Service, 2: Date/Time, 3: Contact, 4: Success

    const searchParams = useSearchParams();

    // Auto-select service from URL
    useEffect(() => {
        const serviceIdParam = searchParams.get('service');
        if (serviceIdParam && services.length > 0 && step === 1) {
            const serviceId = parseInt(serviceIdParam);
            const found = services.find(s => s.id === serviceId);
            if (found) {
                setSelectedService(found);
                setStep(2); // Jump to next step
            }
        }
    }, [searchParams, services, step]);

    // Selection State
    const [selectedService, setSelectedService] = useState<Service | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>("");
    const [selectedTime, setSelectedTime] = useState<string>("");
    const [availableSlots, setAvailableSlots] = useState<string[]>([]);
    const [slotsLoading, setSlotsLoading] = useState(false);

    // Contact Form State
    const [contact, setContact] = useState({
        name: "",
        email: "",
        phone: "",
    });

    const [submitting, setSubmitting] = useState(false);
    const [successData, setSuccessData] = useState<{ id: number } | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchServices();
    }, [params.workspace]);

    // Fetch Slots when Date/Service changes
    useEffect(() => {
        if (selectedService && selectedDate) {
            fetchSlots();
        }
    }, [selectedDate, selectedService]);

    const fetchServices = async () => {
        try {
            // Use the public bookings endpoint to get services
            const res = await api.get(`/api/bookings/services/${params.workspace}`);
            setServices(res.data);
        } catch (error) {
            console.error("Failed to load services", error);
            setError("Could not load services. Please check the workspace link.");
        } finally {
            setLoading(false);
        }
    };

    const fetchSlots = async () => {
        if (!selectedService || !selectedDate) return;

        setSlotsLoading(true);
        setAvailableSlots([]);
        setSelectedTime("");

        try {
            // Calls the PUBLIC availability endpoint we implemented
            const res = await api.get(`/api/public/services/${selectedService.id}/availability`, {
                params: { date: selectedDate }
            });
            setAvailableSlots(res.data);
        } catch (error) {
            console.error("Failed to load slots", error);
        } finally {
            setSlotsLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedService || !selectedDate || !selectedTime) return;

        setSubmitting(true);
        setError("");

        try {
            // Construct ISO datetime from Date + Time
            const start_datetime = new Date(`${selectedDate}T${selectedTime}:00`).toISOString();

            const payload = {
                service_id: selectedService.id,
                start_datetime: start_datetime,
                name: contact.name,
                email: contact.email,
                phone: contact.phone
            };

            const res = await api.post("/api/bookings", payload);
            setSuccessData(res.data);
            setStep(4);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Booking failed. Slot might be taken.");
        } finally {
            setSubmitting(false);
        }
    };

    // --- RENDERERS ---

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50">
                <Spinner className="h-8 w-8 text-indigo-600" />
            </div>
        );
    }

    if (step === 4 && successData) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <Card className="max-w-md w-full text-center p-6 shadow-xl border-green-100">
                    <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
                        <CheckCircle className="h-10 w-10 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Booking Confirmed!</h2>
                    <p className="text-gray-500 mb-8">
                        Please check your email <strong>{contact.email}</strong> for confirmation details and next steps.
                    </p>

                    <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left space-y-2 border">
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Service</span>
                            <span className="text-sm font-medium">{selectedService?.name}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Date</span>
                            <span className="text-sm font-medium">{new Date(selectedDate).toLocaleDateString()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Time</span>
                            <span className="text-sm font-medium">{selectedTime}</span>
                        </div>
                    </div>

                    <Button
                        onClick={() => window.location.reload()}
                        variant="outline"
                        className="w-full"
                    >
                        Book Another
                    </Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex justify-between items-center text-sm font-medium text-gray-500 mb-2">
                        <span className={step >= 1 ? "text-indigo-600" : ""}>Service</span>
                        <span className={step >= 2 ? "text-indigo-600" : ""}>Time</span>
                        <span className={step >= 3 ? "text-indigo-600" : ""}>Details</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-indigo-600 transition-all duration-500 ease-in-out"
                            style={{ width: `${((step - 1) / 2) * 100}%` }}
                        />
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden min-h-[500px] flex flex-col">
                    {/* Header */}
                    <div className="p-6 border-b bg-white">
                        <h1 className="text-2xl font-bold text-gray-900">
                            {step === 1 && "Select a Service"}
                            {step === 2 && "Choose a Time"}
                            {step === 3 && "Your Details"}
                        </h1>
                        <p className="text-gray-500 text-sm mt-1">
                            Booking for workspace: <span className="font-medium text-gray-900">{params.workspace}</span>
                        </p>
                    </div>

                    {/* Content Body */}
                    <div className="p-6 flex-1">
                        {error && (
                            <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-100 flex items-center gap-2">
                                <span className="font-bold">Error:</span> {error}
                            </div>
                        )}

                        {/* STEP 1: SERVICE SELECTION */}
                        {step === 1 && (
                            <div className="grid gap-4 md:grid-cols-2">
                                {services.length === 0 ? (
                                    <p className="text-gray-500 col-span-2 text-center py-10">No services available.</p>
                                ) : services.map(service => (
                                    <div
                                        key={service.id}
                                        onClick={() => setSelectedService(service)}
                                        className={`
                                    cursor-pointer rounded-xl border p-4 transition-all duration-200
                                    ${selectedService?.id === service.id
                                                ? "border-indigo-600 bg-indigo-50 ring-1 ring-indigo-600"
                                                : "border-gray-200 hover:border-indigo-300 hover:bg-gray-50"}
                                `}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="font-semibold text-gray-900">{service.name}</h3>
                                            {selectedService?.id === service.id && <CheckCircle className="h-5 w-5 text-indigo-600" />}
                                        </div>
                                        <div className="space-y-1 text-sm text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-4 h-4" />
                                                <span>{service.duration_minutes} mins</span>
                                            </div>
                                            {service.location && (
                                                <div className="flex items-center gap-2">
                                                    <MapPin className="w-4 h-4" />
                                                    <span>{service.location}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* STEP 2: DATE & TIME */}
                        {step === 2 && (
                            <div className="space-y-6">
                                <div className="flex flex-col md:flex-row gap-6">
                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Pick a Date</label>
                                        <input
                                            type="date"
                                            required
                                            min={new Date().toISOString().split("T")[0]}
                                            value={selectedDate}
                                            onChange={(e) => setSelectedDate(e.target.value)}
                                            className="w-full p-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-medium"
                                        />
                                    </div>

                                    <div className="flex-1">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Available Slots {selectedDate && `for ${new Date(selectedDate).toLocaleDateString()}`}
                                        </label>

                                        {slotsLoading ? (
                                            <div className="flex items-center justify-center h-32 border rounded-lg border-dashed">
                                                <Spinner className="h-6 w-6 text-indigo-600" />
                                            </div>
                                        ) : !selectedDate ? (
                                            <div className="flex items-center justify-center h-32 border rounded-lg border-dashed text-gray-400 bg-gray-50 text-sm">
                                                Select a date to view slots
                                            </div>
                                        ) : availableSlots.length === 0 ? (
                                            <div className="flex items-center justify-center h-32 border rounded-lg border-dashed text-gray-500 bg-gray-50 text-sm">
                                                No slots available for this date
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-3 gap-2 max-h-[300px] overflow-y-auto pr-2">
                                                {availableSlots.map(time => (
                                                    <button
                                                        key={time}
                                                        onClick={() => setSelectedTime(time)}
                                                        className={`
                                                    py-2 px-3 text-sm font-medium rounded-md transition-all
                                                    ${selectedTime === time
                                                                ? "bg-indigo-600 text-white shadow-md transform scale-105"
                                                                : "bg-white border border-gray-200 text-gray-700 hover:border-indigo-400 hover:bg-indigo-50"}
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
                                    <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 flex items-center gap-3 text-indigo-700 text-sm animate-in fade-in slide-in-from-bottom-2">
                                        <CheckCircle className="h-5 w-5" />
                                        <span>You selected <strong>{new Date(selectedDate).toLocaleDateString()}</strong> at <strong>{selectedTime}</strong></span>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* STEP 3: CONTACT FORM */}
                        {step === 3 && (
                            <div className="max-w-lg mx-auto space-y-4">
                                <div className="grid gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                        <input
                                            type="text"
                                            required
                                            value={contact.name}
                                            onChange={(e) => setContact({ ...contact, name: e.target.value })}
                                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="Jane Doe"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                                        <input
                                            type="email"
                                            required
                                            value={contact.email}
                                            onChange={(e) => setContact({ ...contact, email: e.target.value })}
                                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="jane@example.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number (Optional)</label>
                                        <input
                                            type="tel"
                                            value={contact.phone}
                                            onChange={(e) => setContact({ ...contact, phone: e.target.value })}
                                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="+1 (555) 000-0000"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Footer / Navigation */}
                    <div className="p-6 border-t bg-gray-50 flex justify-between items-center">
                        {step > 1 ? (
                            <Button variant="outline" onClick={() => setStep(step - 1)} disabled={submitting}>
                                <ArrowLeft className="mr-2 h-4 w-4" /> Back
                            </Button>
                        ) : (
                            <div></div>
                        )}

                        {step === 1 && (
                            <Button onClick={() => setStep(2)} disabled={!selectedService}>
                                Next <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        )}

                        {step === 2 && (
                            <Button onClick={() => setStep(3)} disabled={!selectedTime}>
                                Next <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        )}

                        {step === 3 && (
                            <Button onClick={handleSubmit} disabled={submitting || !contact.name || !contact.email} className="bg-indigo-600 hover:bg-indigo-700">
                                {submitting ? (
                                    <>
                                        <Spinner className="mr-2 h-4 w-4" /> Confirming...
                                    </>
                                ) : (
                                    <>
                                        Confirm Booking <CheckCircle className="ml-2 h-4 w-4" />
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
