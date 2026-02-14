import { LucideIcon } from "lucide-react";
import { Button } from "./button";

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-12 text-center rounded-lg border-2 border-dashed border-gray-100 bg-gray-50/50">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-100 mb-4">
                <Icon className="h-10 w-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500 max-w-sm mt-1 mb-6">{description}</p>
            {actionLabel && onAction && (
                <Button onClick={onAction}>
                    {actionLabel}
                </Button>
            )}
        </div>
    );
}
