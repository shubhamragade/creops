"use client";

import GmailSettings from '@/components/settings/GmailSettings';

export default function SettingsPage() {
    return (
        <div className="p-8 max-w-4xl">
            <h1 className="text-2xl font-bold mb-6">Workspace Settings</h1>

            <div className="space-y-6">
                <GmailSettings />

                {/* Add more settings sections here as needed */}
            </div>
        </div>
    );
}
