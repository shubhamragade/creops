"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

interface DialogProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children: React.ReactNode;
    footer?: React.ReactNode;
}

export function Dialog({ isOpen, onClose, title, description, children, footer }: DialogProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-2">
                        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-full transition-colors">
                            <X className="h-5 w-5 text-gray-500" />
                        </button>
                    </div>
                    {description && (
                        <p className="text-sm text-gray-500 mb-6">{description}</p>
                    )}
                    <div className="py-2">
                        {children}
                    </div>
                </div>
                {footer && (
                    <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                        {footer}
                    </div>
                )}
            </div>
        </div>
    );
}

// Helper for Confirmation Dialogs
export function ConfirmDialog({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = "Confirm",
    variant = "default",
    loading = false
}: {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmText?: string;
    variant?: "default" | "destructive" | "success";
    loading?: boolean;
}) {
    return (
        <Dialog
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            footer={
                <>
                    <Button variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
                    <Button
                        variant={variant === 'success' ? 'default' : variant}
                        className={variant === 'success' ? 'bg-green-600 hover:bg-green-700' : ''}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? "Processing..." : confirmText}
                    </Button>
                </>
            }
        >
            <p className="text-sm text-gray-600">{message}</p>
        </Dialog>
    );
}
