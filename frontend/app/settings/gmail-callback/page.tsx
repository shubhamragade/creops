'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

import { Suspense } from 'react';

function GmailCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
    const [message, setMessage] = useState('Connecting to Gmail...');

    useEffect(() => {
        handleCallback();
    }, []);

    const handleCallback = async () => {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
            setStatus('error');
            setMessage('Authorization denied. Please try again.');
            setTimeout(() => router.push('/settings'), 3000);
            return;
        }

        if (!code || !state) {
            setStatus('error');
            setMessage('Invalid callback parameters');
            setTimeout(() => router.push('/settings'), 3000);
            return;
        }

        try {
            await api.post('/api/gmail/callback', { code, state });
            setStatus('success');
            setMessage('Gmail connected successfully!');
            setTimeout(() => router.push('/settings'), 2000);
        } catch (error) {
            console.error('OAuth callback failed:', error);
            setStatus('error');
            setMessage('Failed to connect Gmail. Please try again.');
            setTimeout(() => router.push('/settings'), 3000);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
                <div className="text-center">
                    {status === 'processing' && (
                        <>
                            <Loader2 className="h-12 w-12 text-indigo-600 mx-auto animate-spin" />
                            <h2 className="mt-4 text-xl font-semibold text-gray-900">
                                Connecting Gmail
                            </h2>
                            <p className="mt-2 text-sm text-gray-500">
                                Please wait while we complete the connection...
                            </p>
                        </>
                    )}

                    {status === 'success' && (
                        <>
                            <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto" />
                            <h2 className="mt-4 text-xl font-semibold text-gray-900">
                                Success!
                            </h2>
                            <p className="mt-2 text-sm text-gray-500">
                                {message}
                            </p>
                            <p className="mt-4 text-xs text-gray-400">
                                Redirecting to settings...
                            </p>
                        </>
                    )}

                    {status === 'error' && (
                        <>
                            <XCircle className="h-12 w-12 text-red-600 mx-auto" />
                            <h2 className="mt-4 text-xl font-semibold text-gray-900">
                                Connection Failed
                            </h2>
                            <p className="mt-2 text-sm text-gray-500">
                                {message}
                            </p>
                            <p className="mt-4 text-xs text-gray-400">
                                Redirecting to settings...
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function GmailCallbackPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <GmailCallbackContent />
        </Suspense>
    );
}
