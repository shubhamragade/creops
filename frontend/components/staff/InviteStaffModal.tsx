"use client";

import { useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { StaffInvite } from "@/types/staff";
import { Loader2, Plus, Mail } from "lucide-react";
import api from "@/lib/api";

interface InviteStaffModalProps {
    onInviteSuccess: () => void;
}

export default function InviteStaffModal({ onInviteSuccess }: InviteStaffModalProps) {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState("");
    const [permissions, setPermissions] = useState({
        inbox: true,
        bookings: true,
        leads: true,
        inventory: false,
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload: StaffInvite = {
                email,
                permissions
            };

            await api.post("/api/staff/invite", payload);

            setOpen(false);
            onInviteSuccess();
            setEmail("");
            // Reset permissions if needed
        } catch (error: any) {
            console.error("Failed to invite staff:", error);
            alert(error.response?.data?.detail || "Failed to invite staff member");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Button className="gap-2" onClick={() => setOpen(true)}>
                <Plus className="h-4 w-4" />
                Invite Staff
            </Button>

            <Dialog
                isOpen={open}
                onClose={() => setOpen(false)}
                title="Invite Team Member"
                description="Send an invitation email with login credentials. They will be able to access the dashboard with limits."
                footer={
                    <div className="flex justify-end gap-2 w-full">
                        <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading} onClick={handleSubmit}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Send Invitation
                        </Button>
                    </div>
                }
            >
                <form onSubmit={handleSubmit} className="space-y-4 mt-2">
                    <div className="space-y-2">
                        <label htmlFor="email" className="text-sm font-medium">
                            Email Address
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                            <input
                                id="email"
                                type="email"
                                required
                                placeholder="colleague@example.com"
                                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 pl-9"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-3">
                        <label className="text-sm font-medium">Permissions</label>
                        <div className="space-y-2 border rounded-md p-3">
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={permissions.inbox}
                                    onChange={(e) => setPermissions({ ...permissions, inbox: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                Access Inbox
                            </label>
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={permissions.bookings}
                                    onChange={(e) => setPermissions({ ...permissions, bookings: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                Manage Bookings
                            </label>
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={permissions.leads}
                                    onChange={(e) => setPermissions({ ...permissions, leads: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                View Leads
                            </label>
                            <label className="flex items-center gap-2 text-sm cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={permissions.inventory}
                                    onChange={(e) => setPermissions({ ...permissions, inventory: e.target.checked })}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                Manage Inventory
                            </label>
                        </div>
                    </div>
                </form>
            </Dialog>
        </>
    );
}
