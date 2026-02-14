import { LucideLoader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export const Spinner = ({ className }: { className?: string }) => {
    return <LucideLoader2 className={cn("animate-spin", className)} />;
};
