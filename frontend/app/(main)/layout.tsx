"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/layout/AppSidebar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [role, setRole] = useState<"owner" | "staff" | null>(null);
    const [authorized, setAuthorized] = useState(false);

    useEffect(() => {
        // Run on mount
        const token = localStorage.getItem("access_token");
        const userRole = localStorage.getItem("user_role") as "owner" | "staff" | null;

        if (!token) {
            router.replace("/login");
            return;
        }

        // Simple validation
        if (userRole !== "owner" && userRole !== "staff") {
            // Fallback or error?
            // For MVP, if token exists but role is weird, maybe let them in but Sidebar handles "null" case?
            // Or redirect login.
            // router.replace("/login");
        }

        setRole(userRole);
        setAuthorized(true);
    }, [router]);

    if (!authorized) {
        return null; // Prevent flash of content
    }

    return (
        <div className="flex h-screen bg-gray-50">
            <AppSidebar role={role} />
            <main className="flex-1 overflow-auto bg-gray-50/50">
                {children}
            </main>
        </div>
    );
}
