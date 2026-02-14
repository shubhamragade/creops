'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mail, CheckCircle2, XCircle, ExternalLink } from 'lucide-react';

export default function GmailSettings() {
    const router = useRouter();
    const [connected, setConnected] = useState(false);
    const [email, setEmail] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState(false);

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const response = await api.get('/api/integrations/email/status');
            setConnected(response.data.connected);
            setEmail(response.data.email);
        } catch (error) {
            console.error('Failed to check Gmail status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleConnect = async () => {
        try {
            setConnecting(true);
            const response = await api.get('/api/auth/google/start');

            // Redirect to Google OAuth
            window.location.href = response.data.authorization_url;
        } catch (error) {
            console.error('Failed to start OAuth:', error);
            alert('Failed to connect Gmail. Please try again.');
            setConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm('Are you sure you want to disconnect Gmail? Email automations will stop working.')) {
            return;
        }

        try {
            await api.post('/api/integrations/email/disconnect');
            setConnected(false);
            setEmail(null);
            alert('Gmail disconnected successfully');
        } catch (error) {
            console.error('Failed to disconnect:', error);
            alert('Failed to disconnect Gmail');
        }
    };

    if (loading) {
        return (
            <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-10 bg-gray-200 rounded w-1/2"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
            <div className="px-6 py-5 border-b border-gray-200">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Mail className="h-5 w-5 text-indigo-600" />
                            Gmail Integration
                        </h3>
                        <p className="mt-1 text-sm text-gray-500">
                            Connect your Gmail account to send automated emails
                        </p>
                    </div>
                    {connected ? (
                        <Badge variant="success" className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            Connected
                        </Badge>
                    ) : (
                        <Badge variant="secondary" className="flex items-center gap-1">
                            <XCircle className="h-3 w-3" />
                            Not Connected
                        </Badge>
                    )}
                </div>
            </div>

            <div className="px-6 py-5">
                {connected ? (
                    <div className="space-y-4">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex items-start gap-3">
                                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                                <div className="flex-1">
                                    <h4 className="text-sm font-medium text-green-900">
                                        Gmail Connected
                                    </h4>
                                    <p className="mt-1 text-sm text-green-700">
                                        Your email automations are active and working.
                                    </p>
                                    {email && (
                                        <p className="mt-2 text-xs text-green-600 font-mono">
                                            {email}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <Button
                                variant="outline"
                                onClick={handleDisconnect}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                                Disconnect Gmail
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                            <div className="flex items-start gap-3">
                                <XCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                                <div className="flex-1">
                                    <h4 className="text-sm font-medium text-amber-900">
                                        Gmail Not Connected
                                    </h4>
                                    <p className="mt-1 text-sm text-amber-700">
                                        Connect Gmail to enable:
                                    </p>
                                    <ul className="mt-2 text-sm text-amber-700 list-disc list-inside space-y-1">
                                        <li>Welcome emails for new leads</li>
                                        <li>Booking confirmations</li>
                                        <li>Intake form delivery</li>
                                        <li>Appointment reminders</li>
                                        <li>Inbox replies</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <Button
                            onClick={handleConnect}
                            disabled={connecting}
                            className="bg-indigo-600 hover:bg-indigo-700"
                        >
                            <Mail className="mr-2 h-4 w-4" />
                            {connecting ? 'Connecting...' : 'Connect Gmail'}
                            <ExternalLink className="ml-2 h-4 w-4" />
                        </Button>

                        <p className="text-xs text-gray-500">
                            You'll be redirected to Google to authorize access. We only request permission to send and read emails.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
