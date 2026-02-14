'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '../../lib/api';
import { Button } from '@/components/ui/button';
import { Building2, ArrowRight } from 'lucide-react';

export default function SignupPage() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        business_name: '',
        owner_email: '',
        owner_password: '',
        owner_full_name: '',
        business_phone: '',
        business_address: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await api.post('/api/signup', formData);
            const { access_token, workspace_slug } = response.data;

            localStorage.setItem('access_token', access_token);
            localStorage.setItem('user_role', 'owner');
            localStorage.setItem('workspace_slug', workspace_slug);

            // Redirect to dashboard
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Signup failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="mx-auto h-14 w-14 flex items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-200 mb-4">
                        <Building2 className="h-7 w-7" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                        Start Your Business
                    </h1>
                    <p className="mt-2 text-sm text-gray-600">
                        Create your CareOps workspace in 60 seconds
                    </p>
                </div>

                {/* Form Card */}
                <div className="bg-white px-8 py-10 shadow-sm ring-1 ring-gray-900/5 sm:rounded-2xl">
                    <form className="space-y-5" onSubmit={handleSubmit}>
                        {/* Business Name */}
                        <div>
                            <label htmlFor="business_name" className="block text-sm font-medium text-gray-900">
                                Business Name
                            </label>
                            <input
                                id="business_name"
                                name="business_name"
                                type="text"
                                required
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="Wellness Spa"
                                value={formData.business_name}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Owner Name */}
                        <div>
                            <label htmlFor="owner_full_name" className="block text-sm font-medium text-gray-900">
                                Your Full Name
                            </label>
                            <input
                                id="owner_full_name"
                                name="owner_full_name"
                                type="text"
                                required
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="John Smith"
                                value={formData.owner_full_name}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Email */}
                        <div>
                            <label htmlFor="owner_email" className="block text-sm font-medium text-gray-900">
                                Email Address
                            </label>
                            <input
                                id="owner_email"
                                name="owner_email"
                                type="email"
                                required
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="you@business.com"
                                value={formData.owner_email}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Password */}
                        <div>
                            <label htmlFor="owner_password" className="block text-sm font-medium text-gray-900">
                                Password
                            </label>
                            <input
                                id="owner_password"
                                name="owner_password"
                                type="password"
                                required
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="••••••••"
                                value={formData.owner_password}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Phone (Optional) */}
                        <div>
                            <label htmlFor="business_phone" className="block text-sm font-medium text-gray-900">
                                Phone <span className="text-gray-400 text-xs">(optional)</span>
                            </label>
                            <input
                                id="business_phone"
                                name="business_phone"
                                type="tel"
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="+1 (555) 123-4567"
                                value={formData.business_phone}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Address (Optional) */}
                        <div>
                            <label htmlFor="business_address" className="block text-sm font-medium text-gray-900">
                                Business Address <span className="text-gray-400 text-xs">(optional)</span>
                            </label>
                            <input
                                id="business_address"
                                name="business_address"
                                type="text"
                                className="mt-2 block w-full rounded-lg border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm"
                                placeholder="123 Main St, City, State"
                                value={formData.business_address}
                                onChange={handleChange}
                            />
                        </div>

                        {error && (
                            <div className="rounded-lg bg-red-50 p-3">
                                <p className="text-sm text-red-800">{error}</p>
                            </div>
                        )}

                        <Button
                            type="submit"
                            className="w-full bg-indigo-600 hover:bg-indigo-700 h-11 text-base"
                            disabled={loading}
                        >
                            {loading ? 'Creating...' : (
                                <>
                                    Create Workspace
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </>
                            )}
                        </Button>
                    </form>

                    <p className="mt-6 text-center text-sm text-gray-500">
                        Already have an account?{' '}
                        <a href="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                            Sign in
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}
