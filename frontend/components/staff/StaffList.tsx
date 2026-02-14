"use client";

import { useEffect, useState } from "react";
import { Staff } from "@/types/staff";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, User, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StaffListProps {
    refreshTrigger: number;
}

export default function StaffList({ refreshTrigger }: StaffListProps) {
    const [staff, setStaff] = useState<Staff[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStaff();
    }, [refreshTrigger]);

    const fetchStaff = async () => {
        try {
            const response = await api.get("/api/staff/");
            setStaff(response.data);
        } catch (error) {
            console.error("Failed to fetch staff:", error);
        } finally {
            setLoading(false);
        }
    };

    const [openMenuId, setOpenMenuId] = useState<number | null>(null);

    // Close menu when clicking outside (simple version)
    useEffect(() => {
        const handleClickOutside = () => setOpenMenuId(null);
        if (openMenuId) {
            document.addEventListener('click', handleClickOutside);
        }
        return () => document.removeEventListener('click', handleClickOutside);
    }, [openMenuId]);

    if (loading) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    if (staff.length === 0) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center p-8 text-center">
                    <div className="bg-indigo-50 p-4 rounded-full mb-4">
                        <User className="h-8 w-8 text-indigo-600" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">No staff members yet</h3>
                    <p className="text-gray-500 mt-1 max-w-sm">
                        Invite your team members to help manage bookings, leads, and inventory.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Team Members</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Email</th>
                                <th className="px-6 py-3">Role</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {staff.map((member) => (
                                <tr key={member.id} className="bg-white border-b hover:bg-gray-50">
                                    <td className="px-6 py-4 font-medium text-gray-900">
                                        {member.full_name || "Pending Acceptance"}
                                    </td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {member.email}
                                    </td>
                                    <td className="px-6 py-4">
                                        <Badge variant="outline" className="capitalize">
                                            {member.role}
                                        </Badge>
                                    </td>
                                    <td className="px-6 py-4">
                                        <Badge variant={member.is_active ? "default" : "secondary"}>
                                            {member.is_active ? "Active" : "Inactive"}
                                        </Badge>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="relative inline-block text-left" onClick={(e) => e.stopPropagation()}>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => setOpenMenuId(openMenuId === member.id ? null : member.id)}
                                            >
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>

                                            {openMenuId === member.id && (
                                                <div className="absolute right-0 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                                                    <div className="py-1">
                                                        <button
                                                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                                            onClick={async () => {
                                                                if (confirm(`Resend invite to ${member.email}?`)) {
                                                                    try {
                                                                        await api.post(`/api/staff/${member.id}/resend-invite`);
                                                                        alert("Invite resent successfully.");
                                                                    } catch (e) {
                                                                        console.error(e);
                                                                        alert("Failed to resend invite.");
                                                                    }
                                                                }
                                                                setOpenMenuId(null);
                                                            }}
                                                        >
                                                            Resend Invite
                                                        </button>
                                                        <button
                                                            className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                                            onClick={async () => {
                                                                if (confirm(`Are you sure you want to remove ${member.full_name}? They will be deactivated.`)) {
                                                                    try {
                                                                        await api.delete(`/api/staff/${member.id}`);
                                                                        fetchStaff(); // Refresh list
                                                                    } catch (e) {
                                                                        console.error(e);
                                                                        alert("Failed to remove staff.");
                                                                    }
                                                                }
                                                                setOpenMenuId(null);
                                                            }}
                                                        >
                                                            Remove Staff
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    );
}
