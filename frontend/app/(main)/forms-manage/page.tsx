'use client';

import { useState, useEffect } from 'react';
import api from '../../../lib/api';
import { FileText, Plus, Pencil, Trash2, X, Save, ExternalLink, Link2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FormField {
    name: string;
    label: string;
    type: string;
    required: boolean;
}

interface FormItem {
    id: number;
    name: string;
    type: string;
    is_public: boolean;
    fields: FormField[];
    google_form_url?: string;
}

export default function FormsPage() {
    const [forms, setForms] = useState<FormItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    // Add form state
    const [newName, setNewName] = useState('');
    const [newGoogleUrl, setNewGoogleUrl] = useState('');
    const [newFields, setNewFields] = useState<FormField[]>([]);

    // Edit state
    const [editName, setEditName] = useState('');
    const [editGoogleUrl, setEditGoogleUrl] = useState('');
    const [editFields, setEditFields] = useState<FormField[]>([]);

    useEffect(() => {
        fetchForms();
    }, []);

    const fetchForms = async () => {
        try {
            const res = await api.get('/api/forms');
            setForms(res.data);
        } catch (err) {
            console.error('Failed to load forms:', err);
        } finally {
            setLoading(false);
        }
    };

    const addField = (target: 'new' | 'edit') => {
        const field: FormField = { name: '', label: '', type: 'text', required: false };
        if (target === 'new') setNewFields([...newFields, field]);
        else setEditFields([...editFields, field]);
    };

    const updateField = (target: 'new' | 'edit', index: number, key: keyof FormField, value: any) => {
        const setter = target === 'new' ? setNewFields : setEditFields;
        const fields = target === 'new' ? [...newFields] : [...editFields];
        (fields[index] as any)[key] = value;
        // Auto-generate name from label
        if (key === 'label') {
            fields[index].name = value.toLowerCase().replace(/[^a-z0-9]/g, '_');
        }
        setter(fields);
    };

    const removeField = (target: 'new' | 'edit', index: number) => {
        const setter = target === 'new' ? setNewFields : setEditFields;
        const fields = target === 'new' ? [...newFields] : [...editFields];
        fields.splice(index, 1);
        setter(fields);
    };

    const handleAdd = async () => {
        if (!newName.trim()) return;
        try {
            await api.post('/api/forms', {
                name: newName,
                type: 'intake',
                fields: newFields,
                google_form_url: newGoogleUrl || null,
            });
            setNewName('');
            setNewGoogleUrl('');
            setNewFields([]);
            setShowAddForm(false);
            fetchForms();
        } catch (err) {
            console.error('Failed to create form:', err);
        }
    };

    const startEdit = (form: FormItem) => {
        setEditingId(form.id);
        setEditName(form.name);
        setEditGoogleUrl(form.google_form_url || '');
        setEditFields(form.fields || []);
    };

    const handleUpdate = async () => {
        if (!editingId) return;
        try {
            await api.patch(`/api/forms/${editingId}`, {
                name: editName,
                fields: editFields,
                google_form_url: editGoogleUrl || null,
            });
            setEditingId(null);
            fetchForms();
        } catch (err) {
            console.error('Failed to update:', err);
        }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
        try {
            await api.delete(`/api/forms/${id}`);
            fetchForms();
        } catch (err) {
            console.error('Failed to delete:', err);
        }
    };

    const renderFieldEditor = (target: 'new' | 'edit', fields: FormField[]) => (
        <div className="space-y-3 mt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Form Fields</p>
            {fields.map((field, i) => (
                <div key={i} className="flex items-center gap-2 bg-white rounded-lg border p-2">
                    <input
                        type="text"
                        placeholder="Label"
                        className="flex-1 rounded border px-2 py-1 text-sm"
                        value={field.label}
                        onChange={(e) => updateField(target, i, 'label', e.target.value)}
                    />
                    <select
                        className="rounded border px-2 py-1 text-sm"
                        value={field.type}
                        onChange={(e) => updateField(target, i, 'type', e.target.value)}
                    >
                        <option value="text">Text</option>
                        <option value="textarea">Long Text</option>
                        <option value="email">Email</option>
                        <option value="phone">Phone</option>
                    </select>
                    <label className="flex items-center gap-1 text-xs text-gray-600">
                        <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(target, i, 'required', e.target.checked)}
                        />
                        Required
                    </label>
                    <button onClick={() => removeField(target, i)} className="text-red-400 hover:text-red-600">
                        <X className="h-4 w-4" />
                    </button>
                </div>
            ))}
            <Button size="sm" variant="outline" onClick={() => addField(target)} className="h-7 text-xs">
                <Plus className="h-3 w-3 mr-1" /> Add Field
            </Button>
        </div>
    );

    return (
        <div className="p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <FileText className="h-6 w-6 text-indigo-600" />
                        Forms
                    </h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Create intake forms or link Google Forms for your bookings
                    </p>
                </div>
                <Button onClick={() => setShowAddForm(true)} className="bg-indigo-600 hover:bg-indigo-700">
                    <Plus className="h-4 w-4 mr-2" /> New Form
                </Button>
            </div>

            {/* Add Form Panel */}
            {showAddForm && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5 mb-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Create New Form</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Form Name <span className="text-red-500">*</span></label>
                            <input
                                type="text"
                                className="w-full rounded-lg border p-2 text-sm"
                                placeholder="e.g. Client Intake Form"
                                value={newName}
                                onChange={(e) => setNewName(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                <Link2 className="h-4 w-4" /> Google Form URL (optional)
                            </label>
                            <input
                                type="url"
                                className="w-full rounded-lg border p-2 text-sm"
                                placeholder="https://docs.google.com/forms/d/..."
                                value={newGoogleUrl}
                                onChange={(e) => setNewGoogleUrl(e.target.value)}
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Paste a Google Form URL to use instead of built-in fields
                            </p>
                        </div>
                        {!newGoogleUrl && renderFieldEditor('new', newFields)}
                    </div>
                    <div className="flex gap-2 mt-4">
                        <Button
                            onClick={handleAdd}
                            disabled={!newName.trim()}
                            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                        >
                            <Plus className="h-4 w-4 mr-1" /> Create Form
                        </Button>
                        <Button variant="outline" onClick={() => { setShowAddForm(false); setNewFields([]); setNewGoogleUrl(''); }}>
                            <X className="h-4 w-4 mr-1" /> Cancel
                        </Button>
                    </div>
                </div>
            )}

            {/* Forms List */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading forms...</div>
            ) : forms.length === 0 ? (
                <div className="text-center py-16 bg-gray-50 rounded-xl border">
                    <FileText className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-3 text-sm font-medium text-gray-900">No forms yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                        Create intake forms or link Google Forms for customers to fill after booking.
                    </p>
                    <Button onClick={() => setShowAddForm(true)} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                        <Plus className="h-4 w-4 mr-2" /> Create First Form
                    </Button>
                </div>
            ) : (
                <div className="space-y-4">
                    {forms.map((form) => {
                        const isEditing = editingId === form.id;

                        return (
                            <div key={form.id} className={`bg-white shadow-sm ring-1 ring-gray-900/5 rounded-xl p-6 ${isEditing ? 'ring-indigo-300 bg-indigo-50/30' : ''}`}>
                                {isEditing ? (
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Form Name</label>
                                            <input type="text" className="w-full rounded-lg border p-2 text-sm" value={editName} onChange={(e) => setEditName(e.target.value)} />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                                                <Link2 className="h-4 w-4" /> Google Form URL
                                            </label>
                                            <input type="url" className="w-full rounded-lg border p-2 text-sm" placeholder="https://docs.google.com/forms/d/..." value={editGoogleUrl} onChange={(e) => setEditGoogleUrl(e.target.value)} />
                                        </div>
                                        {!editGoogleUrl && renderFieldEditor('edit', editFields)}
                                        <div className="flex gap-2">
                                            <Button size="sm" onClick={handleUpdate} className="bg-green-600 hover:bg-green-700">
                                                <Save className="h-3.5 w-3.5 mr-1" /> Save
                                            </Button>
                                            <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>
                                                <X className="h-3.5 w-3.5 mr-1" /> Cancel
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3">
                                                <h3 className="text-base font-semibold text-gray-900">{form.name}</h3>
                                                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                                                    {form.type || 'intake'}
                                                </span>
                                                {form.google_form_url && (
                                                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 flex items-center gap-1">
                                                        <ExternalLink className="h-3 w-3" /> Google Form
                                                    </span>
                                                )}
                                            </div>
                                            {form.google_form_url ? (
                                                <p className="mt-2 text-sm text-blue-600 flex items-center gap-1">
                                                    <Link2 className="h-3.5 w-3.5" />
                                                    <a href={form.google_form_url} target="_blank" rel="noopener noreferrer" className="underline truncate max-w-md">
                                                        {form.google_form_url}
                                                    </a>
                                                </p>
                                            ) : (
                                                <p className="mt-2 text-sm text-gray-500">
                                                    {form.fields?.length || 0} field{(form.fields?.length || 0) !== 1 ? 's' : ''}: {form.fields?.map(f => f.label || f.name).join(', ') || 'No fields'}
                                                </p>
                                            )}
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                className="h-8 px-3 text-indigo-600 hover:bg-indigo-50"
                                                onClick={() => {
                                                    const url = `${window.location.origin}/forms/p/${form.id}`;
                                                    navigator.clipboard.writeText(url);
                                                    alert("Public Form Link Copied!");
                                                }}
                                            >
                                                <ExternalLink className="h-3.5 w-3.5 mr-1" /> Copy Link
                                            </Button>
                                            <Button size="sm" variant="outline" onClick={() => startEdit(form)} className="h-8 px-3">
                                                <Pencil className="h-3.5 w-3.5" />
                                            </Button>
                                            <Button size="sm" variant="outline" onClick={() => handleDelete(form.id, form.name)} className="h-8 px-3 text-red-600 hover:bg-red-50">
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
