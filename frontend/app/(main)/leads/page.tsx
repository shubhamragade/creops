'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '../../../lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users, Mail, Phone, Calendar, Filter } from 'lucide-react';

interface Lead {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    phone: string | null;
    status: string;
    source: string;
    created_at: string;
}

export default function LeadsPage() {
    const router = useRouter();
    const [leads, setLeads] = useState<Lead[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        fetchLeads();
    }, [filter]);

    const fetchLeads = async () => {
        try {
            const params = filter !== 'all' ? { status: filter } : {};
            const response = await api.get('/api/leads', { params });
            setLeads(response.data);
        } catch (error) {
            console.error('Failed to fetch leads:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateStatus = async (leadId: number, newStatus: string) => {
        try {
            await api.patch(`/api/leads/${leadId}/status`, { status: newStatus });
            fetchLeads();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<string, any> = {
            new: 'default',
            contacted: 'secondary',
            booked: 'success'
        };
        return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
    };

    const getSourceBadge = (source: string) => {
        return (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                {source}
            </span>
        );
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                            <Users className="h-6 w-6" />
                            Leads
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Manage and convert your leads to bookings
                        </p>
                    </div>
                    <div className="text-sm text-gray-500">
                        {leads.length} total leads
                    </div>
                </div>

                {/* Filters */}
                <div className="mt-6 flex gap-2">
                    <Button
                        variant={filter === 'all' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('all')}
                    >
                        All
                    </Button>
                    <Button
                        variant={filter === 'new' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('new')}
                    >
                        New
                    </Button>
                    <Button
                        variant={filter === 'contacted' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('contacted')}
                    >
                        Contacted
                    </Button>
                    <Button
                        variant={filter === 'booked' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter('booked')}
                    >
                        Booked
                    </Button>
                </div>
            </div>

            {/* Leads List */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading...</div>
            ) : leads.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <Users className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No leads yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Share your lead form to start collecting contacts
                    </p>
                </div>
            ) : (
                <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Contact
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Email / Phone
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Source
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Created
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {leads.map((lead) => (
                                <tr key={lead.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="font-medium text-gray-900">
                                            {lead.first_name} {lead.last_name}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900 flex items-center gap-1">
                                            <Mail className="h-3 w-3 text-gray-400" />
                                            {lead.email}
                                        </div>
                                        {lead.phone && (
                                            <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                                                <Phone className="h-3 w-3 text-gray-400" />
                                                {lead.phone}
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {getSourceBadge(lead.source)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {getStatusBadge(lead.status)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(lead.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <div className="flex items-center gap-2">
                                            <select
                                                className="rounded border-gray-300 text-sm"
                                                value={lead.status}
                                                onChange={(e) => updateStatus(lead.id, e.target.value)}
                                            >
                                                <option value="new">New</option>
                                                <option value="contacted">Contacted</option>
                                                <option value="booked">Booked</option>
                                            </select>
                                            {lead.status !== 'booked' && (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => router.push(`/bookings/new?lead_id=${lead.id}&email=${lead.email}&name=${lead.first_name} ${lead.last_name}`)}
                                                    className="text-xs"
                                                >
                                                    Convert
                                                </Button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
