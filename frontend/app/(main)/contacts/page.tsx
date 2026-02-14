'use client';

import { useState, useEffect } from 'react';
import api from '../../../lib/api';
import { Badge } from '@/components/ui/badge';
import { Users, Mail, Phone, Calendar } from 'lucide-react';

interface Contact {
    id: number;
    first_name: string;
    last_name: string;
    full_name: string;
    email: string;
    phone: string | null;
    status: string;
    source: string;
    created_at: string;
}

export default function ContactsPage() {
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchContacts();
    }, []);

    const fetchContacts = async () => {
        try {
            const response = await api.get('/api/leads');
            setContacts(response.data);
        } catch (error) {
            console.error('Failed to fetch contacts:', error);
        } finally {
            setLoading(false);
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

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Users className="h-6 w-6" />
                    Customers
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                    All your customers and leads in one place
                </p>
            </div>

            {/* Contacts List */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading...</div>
            ) : contacts.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <Users className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No customers yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Customers will appear here when they book or fill out your lead form
                    </p>
                </div>
            ) : (
                <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl overflow-hidden">
                    <div className="px-4 py-5 sm:p-6">
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {contacts.map((contact) => (
                                <div
                                    key={contact.id}
                                    className="relative rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm hover:border-gray-300"
                                >
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="text-sm font-medium text-gray-900">
                                            {contact.first_name} {contact.last_name}
                                        </h3>
                                        {getStatusBadge(contact.status)}
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center text-sm text-gray-500">
                                            <Mail className="mr-2 h-4 w-4" />
                                            {contact.email}
                                        </div>
                                        {contact.phone && (
                                            <div className="flex items-center text-sm text-gray-500">
                                                <Phone className="mr-2 h-4 w-4" />
                                                {contact.phone}
                                            </div>
                                        )}
                                        <div className="flex items-center text-sm text-gray-500">
                                            <Calendar className="mr-2 h-4 w-4" />
                                            {new Date(contact.created_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <div className="mt-3">
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                            {contact.source}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
