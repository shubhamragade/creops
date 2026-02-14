"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StaffList from "@/components/staff/StaffList";
import InviteStaffModal from "@/components/staff/InviteStaffModal";

export default function StaffManagementPage() {
    const router = useRouter();
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    useEffect(() => {
        // Ensure only owners can access this page
        // (Backend also protects it, but good for UX)
        const role = localStorage.getItem("user_role");
        if (role === "staff") {
            router.replace("/dashboard"); // Redirect to dashboard, not /staff which might loop
        }
    }, [router]);

    const handleInviteSuccess = () => {
        setRefreshTrigger(prev => prev + 1);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Staff Management</h1>
                    <p className="text-gray-500">Manage your team members and their permissions.</p>
                </div>
                <InviteStaffModal onInviteSuccess={handleInviteSuccess} />
            </div>

            <StaffList refreshTrigger={refreshTrigger} />
        </div>
    );
}
