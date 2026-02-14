"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import {
    Copy,
    ExternalLink,
    Loader2,
    Sparkles,
    Plus,
    Trash2,
    X,
    Clock,
    DollarSign,
    Zap
} from "lucide-react";
import { useToast } from "@/components/ui/toast-context";

interface Service {
    id: number;
    name: string;
    duration_minutes: number;
    price?: number;
    description?: string;
}

export default function ServicesPage() {
    const { showToast } = useToast();
    const [loading, setLoading] = useState(true);
    const [services, setServices] = useState<Service[]>([]);
    const [workspaceSlug, setWorkspaceSlug] = useState<string>("");

    // Create Modal State
    const [showCreate, setShowCreate] = useState(false);
    const [creating, setCreating] = useState(false);
    const [newItem, setNewItem] = useState({
        name: "",
        duration_minutes: 60,
        price: 0,
        description: ""
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // 1. Get Workspace Slug
            const dashRes = await api.get("/api/dashboard");
            setWorkspaceSlug(dashRes.data.workspace_slug);

            // 2. Get Services (Authenticated Owner List)
            const res = await api.get("/api/services");
            setServices(res.data);
        } catch (error) {
            console.error("Failed to load services", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!newItem.name) return;
        setCreating(true);
        try {
            await api.post("/api/services", newItem);
            setShowCreate(false);
            setNewItem({ name: "", duration_minutes: 60, price: 0, description: "" });
            showToast("Service created successfully", "success");
            loadData(); // Refresh list
        } catch (error) {
            console.error(error);
            showToast("Failed to create service", "error");
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
        try {
            await api.delete(`/api/services/${id}`);
            showToast("Service deleted", "success");
            loadData();
        } catch (error) {
            console.error(error);
            showToast("Failed to delete service", "error");
        }
    };

    const copyLink = (serviceId: number) => {
        if (!workspaceSlug) return;
        const url = `${window.location.origin}/book/${workspaceSlug}?service=${serviceId}`;
        navigator.clipboard.writeText(url);
        // Simple alert or toast
        showToast("Booking Link Copied!", "success");
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    return (
        <div className="p-8 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Zap className="h-6 w-6 text-indigo-600" />
                        Services Manager
                    </h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Create services and get booking links to send to clients.
                    </p>
                </div>
                <Button onClick={() => setShowCreate(true)} className="bg-indigo-600 hover:bg-indigo-700">
                    <Plus className="h-4 w-4 mr-2" /> New Service
                </Button>
            </div>

            {/* Create Modal (Inline for simplicity) */}
            {showCreate && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-in zoom-in-95">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-gray-900">Create Service</h3>
                            <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Service Name</label>
                                <input
                                    autoFocus
                                    type="text"
                                    className="w-full p-2 border rounded-lg"
                                    placeholder="e.g. Laser Hair Removal"
                                    value={newItem.name}
                                    onChange={e => setNewItem({ ...newItem, name: e.target.value })}
                                />
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
                                    <input
                                        type="number"
                                        className="w-full p-2 border rounded-lg"
                                        value={newItem.duration_minutes}
                                        onChange={e => setNewItem({ ...newItem, duration_minutes: parseInt(e.target.value) || 0 })}
                                    />
                                </div>
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                                    <input
                                        type="number"
                                        className="w-full p-2 border rounded-lg"
                                        value={newItem.price}
                                        onChange={e => setNewItem({ ...newItem, price: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
                                <textarea
                                    className="w-full p-2 border rounded-lg h-24 resize-none"
                                    placeholder="Details for the client..."
                                    value={newItem.description}
                                    onChange={e => setNewItem({ ...newItem, description: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="mt-6 flex gap-3 justify-end">
                            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                            <Button onClick={handleCreate} disabled={!newItem.name || creating} className="bg-indigo-600 hover:bg-indigo-700">
                                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Service"}
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services.map((service) => (
                    <Card key={service.id} className="hover:shadow-md transition-shadow flex flex-col">
                        <CardHeader className="pb-3 flex-1">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-lg font-semibold text-gray-900 leading-snug">
                                    {service.name}
                                </CardTitle>
                                <button
                                    onClick={() => handleDelete(service.id, service.name)}
                                    className="text-gray-400 hover:text-red-600 transition-colors p-1"
                                    title="Delete Service"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mt-2">
                                <span className="flex items-center gap-1">
                                    <Clock className="h-3.5 w-3.5" /> {service.duration_minutes}m
                                </span>
                                {service.price !== undefined && service.price > 0 && (
                                    <span className="flex items-center gap-1">
                                        <DollarSign className="h-3.5 w-3.5" /> ${service.price}
                                    </span>
                                )}
                            </div>
                            {service.description && (
                                <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                                    {service.description}
                                </p>
                            )}
                        </CardHeader>
                        <CardContent className="pt-0 pb-3">
                            <Button
                                onClick={() => copyLink(service.id)}
                                className="w-full bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 shadow-sm"
                            >
                                <Copy className="h-4 w-4 mr-2" />
                                Copy Link
                            </Button>
                        </CardContent>
                        <CardFooter className="pt-0 pb-4 border-t bg-gray-50/50 flex items-center justify-center">
                            <button
                                className="text-xs text-gray-500 hover:text-indigo-600 flex items-center gap-1 mt-2"
                                onClick={() => {
                                    const url = `${window.location.origin}/book/${workspaceSlug}?service=${service.id}`;
                                    window.open(url, '_blank');
                                }}
                            >
                                <ExternalLink className="h-3 w-3" /> Preview Booking Page
                            </button>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            {services.length === 0 && !loading && (
                <div className="text-center py-16 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                    <Sparkles className="h-10 w-10 text-gray-400 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-gray-900">No services yet</h3>
                    <p className="text-gray-500 mb-6">Create your first service to get started.</p>
                    <Button onClick={() => setShowCreate(true)} className="bg-indigo-600">
                        <Plus className="h-4 w-4 mr-2" /> Create Service
                    </Button>
                </div>
            )}
        </div>
    );
}
