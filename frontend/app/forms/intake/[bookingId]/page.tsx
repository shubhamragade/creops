'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api'; // Using alias if available, else relative
import { Loader2, CheckCircle2, AlertCircle, MapPin, Calendar, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function IntakeFormPage() {
    const params = useParams();
    const bookingId = params.bookingId;

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    // Data
    const [form, setForm] = useState<any>(null);
    const [bookingDetails, setBookingDetails] = useState<any>(null);
    const [answers, setAnswers] = useState<Record<string, any>>({});

    useEffect(() => {
        if (bookingId) {
            fetchForm();
        }
    }, [bookingId]);

    const fetchForm = async () => {
        try {
            const res = await api.get(`/api/public/bookings/${bookingId}/intake`);
            setForm(res.data.form);
            setBookingDetails({
                customer_name: res.data.customer_name,
                service_name: res.data.service_name,
                date_time: res.data.date_time,
                workspace_name: res.data.workspace_name
            });
            // Initialize answers with pre-filled data if any, otherwise empty strings
            if (res.data.form.pre_filled_answers) {
                setAnswers(res.data.form.pre_filled_answers);
            } else {
                const initial: Record<string, any> = {};
                res.data.form.fields.forEach((f: any) => {
                    initial[f.name] = '';
                });
                setAnswers(initial);
            }
        } catch (err: any) {
            console.error(err);
            setError("Failed to load form. It may not exist or the link is invalid.");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError('');

        try {
            await api.post(`/api/public/bookings/${bookingId}/intake`, {
                answers
            });
            setSuccess(true);
        } catch (err: any) {
            console.error(err);
            setError('Failed to submit form. Please try again.');
            setSubmitting(false);
        }
    };

    const handleInputChange = (field: string, value: string) => {
        setAnswers(prev => ({ ...prev, [field]: value }));
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    if (error && !bookingDetails) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="max-w-md w-full bg-white shadow rounded-lg p-8 text-center">
                    <div className="mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                        <AlertCircle className="h-6 w-6 text-red-600" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Unable to Load Request</h2>
                    <p className="text-gray-600">{error}</p>
                </div>
            </div>
        );
    }

    if (success) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="max-w-md w-full bg-white shadow rounded-lg p-8 text-center">
                    <div className="mx-auto h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                        <CheckCircle2 className="h-6 w-6 text-green-600" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">All set!</h2>
                    <p className="text-gray-600 mb-6">
                        Thank you for completing your intake form.<br />
                        We look forward to seeing you soon.
                    </p>
                    <div className="bg-gray-50 rounded p-4 text-left text-sm text-gray-500">
                        <p>You can close this window now.</p>
                    </div>
                </div>
            </div>
        );
    }

    // New check for form and bookingDetails after loading
    if (!form || !bookingDetails) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="bg-red-50 p-4 rounded-md">
                    <p className="text-red-700">{error || "Form not found"}</p>
                </div>
            </div>
        );
    }

    // Destructure from state variables
    const { workspace_name, service_name, customer_name, date_time } = bookingDetails;
    const dateObj = new Date(date_time);

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-xl mx-auto">
                {/* Header */}
                <div className="text-center mb-10">
                    <h2 className="text-2xl font-bold text-gray-900">{workspace_name}</h2>
                    <p className="mt-2 text-gray-600">Intake Request</p>
                </div>

                {/* Context Card */}
                <div className="bg-white shadow sm:rounded-lg mb-6 overflow-hidden">
                    <div className="px-4 py-5 sm:p-6">
                        <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                            Hi {customer_name},
                        </h3>
                        <p className="text-sm text-gray-500 mb-6">
                            Please provide the following details for your upcoming appointment.
                        </p>

                        <div className="flex flex-col gap-3 bg-indigo-50/50 p-4 rounded-md border border-indigo-100">
                            <div className="flex items-center gap-3 text-sm text-gray-700">
                                <Calendar className="h-4 w-4 text-indigo-600" />
                                <span className="font-medium">
                                    {dateObj.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
                                </span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-gray-700">
                                <Clock className="h-4 w-4 text-indigo-600" />
                                <span className="font-medium">
                                    {dateObj.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}
                                </span>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-gray-700">
                                <div className="h-4 w-4 flex items-center justify-center font-bold text-xs bg-indigo-600 text-white rounded-full">S</div>
                                <span className="font-medium">{service_name}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Form Card */}
                <div className="bg-white shadow sm:rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                        {form.google_form_url ? (
                            <div className="text-center py-8">
                                <p className="text-gray-600 mb-6">
                                    Please complete the intake form securely via Google Forms.
                                </p>
                                <a
                                    href={form.google_form_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                                >
                                    Open Intake Form
                                </a>
                                <p className="mt-4 text-sm text-gray-500">
                                    After submitting, you can close this page.
                                </p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                {form.fields.map((field: any) => (
                                    <div key={field.name}>
                                        <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
                                            {field.label || field.name}
                                            {field.required && <span className="text-red-500 ml-1">*</span>}
                                        </label>
                                        <div className="mt-1">
                                            {field.type === 'textarea' ? (
                                                <textarea
                                                    id={field.name}
                                                    name={field.name}
                                                    rows={4}
                                                    required={field.required}
                                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 border"
                                                    value={answers[field.name] || ''}
                                                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                                                />
                                            ) : (
                                                <input
                                                    type={field.type || 'text'}
                                                    id={field.name}
                                                    name={field.name}
                                                    required={field.required}
                                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm h-10 px-3 border"
                                                    value={answers[field.name] || ''}
                                                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                                                />
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {error && (
                                    <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                                        {error}
                                    </div>
                                )}

                                <div>
                                    <Button
                                        type="submit"
                                        disabled={submitting}
                                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                    >
                                        {submitting ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Submitting...
                                            </>
                                        ) : (
                                            'Submit Information'
                                        )}
                                    </Button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-8 text-center">
                    <p className="text-xs text-gray-400">
                        &copy; {new Date().getFullYear()} {workspace_name}. Secured by CareOps.
                    </p>
                </div>
            </div>
        </div>
    );
}
