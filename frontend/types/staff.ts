
export interface Staff {
    id: number;
    email: string;
    full_name: string;
    is_active: boolean;
    role: 'owner' | 'staff';
    permissions?: Record<string, boolean>;
}

export interface StaffInvite {
    email: string;
    permissions: Record<string, boolean>;
}
