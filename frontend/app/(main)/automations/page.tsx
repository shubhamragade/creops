'use client';

import { useState } from 'react';
import { Zap, Mail, Calendar, Package, CheckCircle2 } from 'lucide-react';

export default function AutomationsPage() {
    const [automations] = useState([
        {
            id: 1,
            name: "New Lead Welcome Email",
            description: "Send welcome email when someone fills the lead form",
            trigger: "Lead Form Submission",
            action: "Send Email",
            active: true,
            icon: Mail
        },
        {
            id: 2,
            name: "Booking Confirmation",
            description: "Send confirmation email immediately after booking",
            trigger: "Booking Created",
            action: "Send Email",
            active: true,
            icon: Mail
        },
        {
            id: 3,
            name: "Intake Form Delivery",
            description: "Send intake form link after booking confirmation",
            trigger: "Booking Confirmed",
            action: "Send Form Link",
            active: true,
            icon: Mail
        },
        {
            id: 4,
            name: "Appointment Reminder",
            description: "Send reminder 24 hours before appointment",
            trigger: "24h Before Booking",
            action: "Send Email",
            active: true,
            icon: Calendar
        },
        {
            id: 5,
            name: "Low Inventory Alert",
            description: "Alert owner when inventory falls below threshold",
            trigger: "Low Stock Detected",
            action: "Send Alert",
            active: true,
            icon: Package
        }
    ]);

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                    <Zap className="h-6 w-6 text-indigo-600" />
                    Automations
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                    Your active automation rules running in the background
                </p>
            </div>

            {/* Automations List */}
            <div className="space-y-4">
                {automations.map((automation) => {
                    const Icon = automation.icon;
                    return (
                        <div
                            key={automation.id}
                            className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl p-6 hover:shadow-md transition-shadow"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="h-10 w-10 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                                        <Icon className="h-5 w-5 text-indigo-600" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3">
                                            <h3 className="text-base font-semibold text-gray-900">
                                                {automation.name}
                                            </h3>
                                            {automation.active && (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    <CheckCircle2 className="h-3 w-3" />
                                                    Active
                                                </span>
                                            )}
                                        </div>
                                        <p className="mt-1 text-sm text-gray-600">
                                            {automation.description}
                                        </p>
                                        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                                            <div className="flex items-center gap-1">
                                                <span className="font-medium">Trigger:</span>
                                                <span className="px-2 py-0.5 rounded bg-gray-100">
                                                    {automation.trigger}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <span className="font-medium">Action:</span>
                                                <span className="px-2 py-0.5 rounded bg-gray-100">
                                                    {automation.action}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Info Box */}
            <div className="mt-8 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Zap className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-medium text-indigo-900">
                            Automation Status
                        </h4>
                        <p className="mt-1 text-sm text-indigo-700">
                            All {automations.length} automations are currently active and running in the background.
                            They will execute automatically based on their triggers.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
