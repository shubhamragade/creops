"use client";

import { useSearchParams, useParams } from "next/navigation";
import { useState, Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/toast-context";

function CancelBookingContent() {
    const searchParams = useSearchParams();
    const params = useParams();
    const bookingId = searchParams.get("booking");
    const token = searchParams.get("token");
    const [isLoading, setIsLoading] = useState(false);
    const [isCancelled, setIsCancelled] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { showToast } = useToast();

    // If no booking ID or token, show invalid link
    if (!bookingId || !token) {
        return (
            <Card className="w-full max-w-md mx-auto mt-10 shadow-lg border-red-100">
                <CardHeader>
                    <div className="mx-auto bg-red-100 p-3 rounded-full mb-4">
                        <XCircle className="h-8 w-8 text-red-600" />
                    </div>
                    <CardTitle className="text-center text-red-700">Invalid Link</CardTitle>
                    <CardDescription className="text-center">
                        This cancellation link is incomplete or invalid. Please check your email and try again.
                    </CardDescription>
                </CardHeader>
            </Card>
        );
    }

    const handleCancel = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/bookings/${bookingId}/cancel?token=${encodeURIComponent(token)}`, {
                method: "POST",
            });

            const data = await response.json();

            if (!response.ok) {
                if (data.status === "already_cancelled") {
                    setIsCancelled(true);
                    showToast("This booking was already cancelled.", "info");
                    return;
                }
                throw new Error(data.detail || "Failed to cancel booking");
            }

            setIsCancelled(true);
            showToast("Your booking has been successfully cancelled.", "success");

        } catch (err: any) {
            setError(err.message);
            showToast(err.message, "error");
        } finally {
            setIsLoading(false);
        }
    };

    if (isCancelled) {
        return (
            <Card className="w-full max-w-md mx-auto mt-10 shadow-lg border-green-100">
                <CardHeader>
                    <div className="mx-auto bg-green-100 p-3 rounded-full mb-4">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                    </div>
                    <CardTitle className="text-center text-green-700">Cancellation Confirmed</CardTitle>
                    <CardDescription className="text-center">
                        Your appointment has been cancelled successfully. You should receive a confirmation email shortly.
                    </CardDescription>
                </CardHeader>
                <CardFooter className="flex justify-center pb-8">
                    <Button variant="outline" onClick={() => window.close()}>
                        Close Window
                    </Button>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="w-full max-w-md mx-auto mt-10 shadow-lg border-amber-50">
            <CardHeader>
                <div className="mx-auto bg-amber-100 p-3 rounded-full mb-4">
                    <AlertTriangle className="h-8 w-8 text-amber-600" />
                </div>
                <CardTitle className="text-center">Cancel Booking?</CardTitle>
                <CardDescription className="text-center">
                    Are you sure you want to cancel booking #{bookingId}? This action cannot be undone.
                </CardDescription>
            </CardHeader>
            <CardContent>
                {error && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm text-center mb-4">
                        {error}
                    </div>
                )}
            </CardContent>
            <CardFooter className="flex flex-col gap-3 pb-8">
                <Button
                    variant="destructive"
                    className="w-full h-12 text-lg"
                    onClick={handleCancel}
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                            Cancelling...
                        </>
                    ) : (
                        "Confirm Cancellation"
                    )}
                </Button>
                <Button variant="ghost" className="w-full" onClick={() => window.history.back()}>
                    Go Back
                </Button>
            </CardFooter>
        </Card>
    );
}

export default function CancelBookingPage() {
    return (
        <div className="min-h-screen bg-gray-50 p-4 flex items-center justify-center">
            <Suspense fallback={<div className="text-center">Loading...</div>}>
                <CancelBookingContent />
            </Suspense>
        </div>
    );
}
