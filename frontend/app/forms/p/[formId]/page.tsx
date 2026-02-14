'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function PublicFormPage() {
    const params = useParams();
    const formId = params.formId;

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    // Data
    const [form, setForm] = useState<any>(null);
    const [workspaceName, setWorkspaceName] = useState('');
    const [answers, setAnswers] = useState<Record<string, any>>({});

    useEffect(() => {
        if (formId) {
            fetchForm();
        }
    }, [formId]);

    const fetchForm = async () => {
        try {
            const res = await api.get(`/api/public/forms/${formId}`);
            setForm(res.data);
            setWorkspaceName(res.data.workspace_name);

            // Initialize answers
            const initial: Record<string, any> = {};
            res.data.fields.forEach((f: any) => {
                initial[f.name] = '';
            });
            setAnswers(initial);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load form. It may not exist.");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError('');

        try {
            await api.post(`/api/public/forms/${formId}/submit`, {
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

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="max-w-md w-full bg-white shadow rounded-lg p-8 text-center">
                    <div className="mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                        <AlertCircle className="h-6 w-6 text-red-600" />
                    </div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Unable to Load Form</h2>
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
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Thank You!</h2>
                    <p className="text-gray-600 mb-6">
                        We have received your information.<br />
                        Please check your email for the next steps.
                    </p>
                    <div className="bg-gray-50 rounded p-4 text-left text-sm text-gray-500">
                        <p>You can close this window now.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-xl mx-auto">
                {/* Header */}
                <div className="text-center mb-10">
                    <h2 className="text-2xl font-bold text-gray-900">{workspaceName}</h2>
                    <p className="mt-2 text-gray-600">{form?.name}</p>
                </div>

                {/* Form Card */}
                <div className="bg-white shadow sm:rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                        {form?.google_form_url ? (
                            <div className="text-center py-8">
                                <p className="text-gray-600 mb-6">
                                    Please complete the form securely via Google Forms.
                                </p>
                                <a
                                    href={form.google_form_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                                >
                                    Open Form
                                </a>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                {form?.fields.map((field: any) => (
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
                                            'Submit'
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
                        &copy; {new Date().getFullYear()} {workspaceName}. Secured by CareOps.
                    </p>
                </div>
            </div>
        </div>
    );
}
