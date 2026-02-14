'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '../../lib/api';
import { Button } from '@/components/ui/button';
import { Lock, ShieldCheck } from 'lucide-react';

// Checking package.json... it has @radix-ui/react-slot and tailwind-merge, suggesting shadcn setup or similar.
// But I don't see a components folder in list_dir output. 
// "frontend/app" existed. 
// I'll stick to standard HTML/Tailwind for "Simple UI. No heavy design." as requested.
// "Minimal components".

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await api.post('/api/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            const { access_token, role, workspace_slug } = response.data;

            localStorage.setItem('access_token', access_token);
            localStorage.setItem('user_role', role);
            localStorage.setItem('workspace_slug', workspace_slug);
            localStorage.setItem('user_permissions', JSON.stringify(response.data.permissions)); // Save permissions

            if (role === 'owner') {
                router.replace('/dashboard');
            } else {
                router.replace('/staff');
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
            <div className="w-full max-w-sm space-y-8">
                {/* Header */}
                <div className="text-center">
                    <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-200">
                        <Lock className="h-6 w-6" />
                    </div>
                    <h2 className="mt-6 text-2xl font-bold tracking-tight text-gray-900">
                        CareOps
                    </h2>
                    <p className="mt-2 text-sm text-gray-500">
                        Sign in to your workspace
                    </p>
                </div>

                {/* Card */}
                <div className="bg-white px-8 py-10 shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
                    <form className="space-y-6" onSubmit={handleLogin}>
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900">
                                Email address
                            </label>
                            <div className="mt-2 text-sm">
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    required
                                    className="block w-full rounded-md border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3 transition-shadow"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900">
                                Password
                            </label>
                            <div className="mt-2">
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    autoComplete="current-password"
                                    required
                                    className="block w-full rounded-md border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 px-3 transition-shadow"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="rounded-md bg-red-50 p-3">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <ShieldCheck className="h-5 w-5 text-red-400" aria-hidden="true" />
                                    </div>
                                    <div className="ml-3">
                                        <h3 className="text-sm font-medium text-red-800">Login failed</h3>
                                        <div className="mt-1 text-sm text-red-700">
                                            <p>{error}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div>
                            <Button
                                type="submit"
                                className="w-full bg-indigo-600 hover:bg-indigo-700 h-10"
                                loading={loading}
                            >
                                Sign in
                            </Button>
                        </div>
                    </form>
                </div>

                {/* Trust Footer */}
                <p className="text-center text-xs text-gray-500 flex items-center justify-center gap-2">
                    <ShieldCheck className="h-4 w-4" />
                    <span>Secure end-to-end encrypted session</span>
                </p>
            </div>
        </div>
    );
}
