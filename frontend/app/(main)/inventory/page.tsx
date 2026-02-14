'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '../../../lib/api';
import { Package, Plus, Pencil, Trash2, AlertTriangle, CheckCircle2, X, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface InventoryItem {
    id: number;
    name: string;
    quantity: number;
    threshold: number;
}

export default function InventoryPage() {
    const router = useRouter();
    const [items, setItems] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    // Add form state
    const [newName, setNewName] = useState('');
    const [newQuantity, setNewQuantity] = useState(0);
    const [newThreshold, setNewThreshold] = useState(5);

    // Edit state
    const [editName, setEditName] = useState('');
    const [editQuantity, setEditQuantity] = useState(0);
    const [editThreshold, setEditThreshold] = useState(0);

    useEffect(() => {
        const role = localStorage.getItem('user_role');
        if (role === 'staff') {
            router.replace('/staff');
            return;
        }
        fetchItems();
    }, []);

    const fetchItems = async () => {
        try {
            const res = await api.get('/api/inventory');
            setItems(res.data);
        } catch (err) {
            console.error('Failed to load inventory:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async () => {
        if (!newName.trim()) return;
        try {
            await api.post('/api/inventory', {
                name: newName,
                quantity: newQuantity,
                threshold: newThreshold,
            });
            setNewName('');
            setNewQuantity(0);
            setNewThreshold(5);
            setShowAddForm(false);
            fetchItems();
        } catch (err) {
            console.error('Failed to add item:', err);
        }
    };

    const startEdit = (item: InventoryItem) => {
        setEditingId(item.id);
        setEditName(item.name);
        setEditQuantity(item.quantity);
        setEditThreshold(item.threshold);
    };

    const handleUpdate = async () => {
        if (!editingId) return;
        try {
            await api.patch(`/api/inventory/${editingId}`, {
                name: editName,
                quantity: editQuantity,
                threshold: editThreshold,
            });
            setEditingId(null);
            fetchItems();
        } catch (err) {
            console.error('Failed to update:', err);
        }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
        try {
            await api.delete(`/api/inventory/${id}`);
            fetchItems();
        } catch (err) {
            console.error('Failed to delete:', err);
        }
    };

    const getStatus = (item: InventoryItem) => {
        if (item.quantity <= 0) return { label: 'Out of Stock', color: 'bg-red-100 text-red-800', dot: 'bg-red-500' };
        if (item.quantity <= item.threshold) return { label: 'Low Stock', color: 'bg-amber-100 text-amber-800', dot: 'bg-amber-500' };
        return { label: 'In Stock', color: 'bg-green-100 text-green-800', dot: 'bg-green-500' };
    };

    const lowCount = items.filter(i => i.quantity <= i.threshold && i.quantity > 0).length;
    const outCount = items.filter(i => i.quantity <= 0).length;

    return (
        <div className="p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Package className="h-6 w-6 text-indigo-600" />
                        Inventory
                    </h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Track supplies and resources linked to your services
                    </p>
                </div>
                <Button
                    onClick={() => setShowAddForm(true)}
                    className="bg-indigo-600 hover:bg-indigo-700"
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Item
                </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="bg-white rounded-xl border p-4 shadow-sm">
                    <p className="text-sm text-gray-500">Total Items</p>
                    <p className="text-2xl font-bold text-gray-900">{items.length}</p>
                </div>
                <div className="bg-white rounded-xl border p-4 shadow-sm">
                    <p className="text-sm text-amber-600 flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4" /> Low Stock
                    </p>
                    <p className="text-2xl font-bold text-amber-600">{lowCount}</p>
                </div>
                <div className="bg-white rounded-xl border p-4 shadow-sm">
                    <p className="text-sm text-red-600 flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4" /> Out of Stock
                    </p>
                    <p className="text-2xl font-bold text-red-600">{outCount}</p>
                </div>
            </div>

            {/* Add Form */}
            {showAddForm && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5 mb-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Add New Item</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
                            <input
                                type="text"
                                className="w-full rounded-lg border p-2 text-sm"
                                placeholder="e.g. Massage Oil"
                                value={newName}
                                onChange={(e) => setNewName(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                            <input
                                type="number"
                                className="w-full rounded-lg border p-2 text-sm"
                                value={newQuantity}
                                onChange={(e) => setNewQuantity(parseInt(e.target.value) || 0)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Low Threshold</label>
                            <input
                                type="number"
                                className="w-full rounded-lg border p-2 text-sm"
                                value={newThreshold}
                                onChange={(e) => setNewThreshold(parseInt(e.target.value) || 0)}
                            />
                        </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                        <Button onClick={handleAdd} className="bg-indigo-600 hover:bg-indigo-700">
                            <Plus className="h-4 w-4 mr-1" /> Add
                        </Button>
                        <Button variant="outline" onClick={() => setShowAddForm(false)}>
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                    </div>
                </div>
            )}

            {/* Inventory Table */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading inventory...</div>
            ) : items.length === 0 ? (
                <div className="text-center py-16 bg-gray-50 rounded-xl border">
                    <Package className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-3 text-sm font-medium text-gray-900">No inventory items</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Add items to track supplies used by your services.
                    </p>
                    <Button
                        onClick={() => setShowAddForm(true)}
                        className="mt-4 bg-indigo-600 hover:bg-indigo-700"
                    >
                        <Plus className="h-4 w-4 mr-2" /> Add First Item
                    </Button>
                </div>
            ) : (
                <div className="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-xl overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Threshold</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {items.map((item) => {
                                const status = getStatus(item);
                                const isEditing = editingId === item.id;

                                return (
                                    <tr key={item.id} className={isEditing ? 'bg-indigo-50/50' : 'hover:bg-gray-50'}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {isEditing ? (
                                                <input
                                                    type="text"
                                                    className="rounded border px-2 py-1 text-sm w-40"
                                                    value={editName}
                                                    onChange={(e) => setEditName(e.target.value)}
                                                />
                                            ) : (
                                                <span className="text-sm font-medium text-gray-900">{item.name}</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {isEditing ? (
                                                <input
                                                    type="number"
                                                    className="rounded border px-2 py-1 text-sm w-20"
                                                    value={editQuantity}
                                                    onChange={(e) => setEditQuantity(parseInt(e.target.value) || 0)}
                                                />
                                            ) : (
                                                <span className="text-sm text-gray-700">{item.quantity}</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {isEditing ? (
                                                <input
                                                    type="number"
                                                    className="rounded border px-2 py-1 text-sm w-20"
                                                    value={editThreshold}
                                                    onChange={(e) => setEditThreshold(parseInt(e.target.value) || 0)}
                                                />
                                            ) : (
                                                <span className="text-sm text-gray-500">{item.threshold}</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                                                <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`}></span>
                                                {status.label}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                                            {isEditing ? (
                                                <>
                                                    <Button size="sm" onClick={handleUpdate} className="bg-green-600 hover:bg-green-700 h-8 px-3">
                                                        <Save className="h-3.5 w-3.5 mr-1" /> Save
                                                    </Button>
                                                    <Button size="sm" variant="outline" onClick={() => setEditingId(null)} className="h-8 px-3">
                                                        <X className="h-3.5 w-3.5" />
                                                    </Button>
                                                </>
                                            ) : (
                                                <>
                                                    <Button size="sm" variant="outline" onClick={() => startEdit(item)} className="h-8 px-3">
                                                        <Pencil className="h-3.5 w-3.5" />
                                                    </Button>
                                                    <Button size="sm" variant="outline" onClick={() => handleDelete(item.id, item.name)} className="h-8 px-3 text-red-600 hover:bg-red-50">
                                                        <Trash2 className="h-3.5 w-3.5" />
                                                    </Button>
                                                </>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
