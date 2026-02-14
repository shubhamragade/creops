'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import axios from 'axios';

import { Suspense } from 'react';

function GoogleCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
    const [message, setMessage] = useState('Connecting your Gmail account...');
    const processedRef = useRef(false);

    useEffect(() => {
        const handleCallback = async () => {
            if (processedRef.current) return;
            processedRef.current = true;

            const code = searchParams.get('code');
            const state = searchParams.get('state');
            const error = searchParams.get('error');

            if (error) {
                setStatus('error');
                setMessage(`Authorization failed: ${error}`);
                setTimeout(() => router.push('/dashboard/settings'), 3000);
                return;
            }

            if (!code || !state) {
                setStatus('error');
                setMessage('Missing authorization code or state');
                setTimeout(() => router.push('/dashboard/settings'), 3000);
                return;
            }

            try {
                // Call backend callback endpoint
                await axios.get(`http://localhost:8001/api/auth/google/callback`, {
                    params: { code, state }
                });

                setStatus('success');
                setMessage('Gmail connected successfully!');

                // Redirect to settings after 2 seconds
                setTimeout(() => {
                    router.push('/dashboard/settings?connected=true');
                }, 2000);
            } catch (err: any) {
                console.error('Callback error:', err);
                setStatus('error');
                setMessage(err.response?.data?.detail || 'Failed to connect Gmail');
                setTimeout(() => router.push('/dashboard/settings'), 3000);
            }
        };

        handleCallback();
    }, [searchParams, router]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
                {status === 'processing' && (
                    <>
                        <div className="mx-auto h-16 w-16 mb-6">
                            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            Connecting Gmail
                        </h2>
                        <p className="text-gray-600">
                            {message}
                        </p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-green-100 mb-6">
                            <svg className="h-10 w-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            Success!
                        </h2>
                        <p className="text-gray-600">
                            {message}
                        </p>
                        <p className="text-sm text-gray-500 mt-4">
                            Redirecting to settings...
                        </p>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-red-100 mb-6">
                            <svg className="h-10 w-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            Connection Failed
                        </h2>
                        <p className="text-gray-600">
                            {message}
                        </p>
                        <p className="text-sm text-gray-500 mt-4">
                            Redirecting to settings...
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}

export default function GoogleCallbackPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <GoogleCallbackContent />
        </Suspense>
    );
}
