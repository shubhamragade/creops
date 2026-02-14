import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface MetricCardProps {
    title: string;
    value: string | number | undefined;
    subtext?: string;
    icon: LucideIcon;
    trend?: "positive" | "negative" | "neutral";
    href?: string;
    loading?: boolean;
}

export function MetricCard({ title, value, subtext, icon: Icon, trend = "neutral", href, loading }: MetricCardProps) {
    const Content = (
        <Card className="hover:shadow-md transition-all duration-200 cursor-pointer border-gray-200 hover:border-indigo-100 group h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-500 group-hover:text-indigo-600 transition-colors">
                    {title}
                </CardTitle>
                <Icon className="h-4 w-4 text-gray-400 group-hover:text-indigo-500" />
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="space-y-2 animate-pulse">
                        <div className="h-8 w-16 bg-gray-100 rounded" />
                        <div className="h-3 w-24 bg-gray-50 rounded" />
                    </div>
                ) : (
                    <>
                        <div className="text-2xl font-bold text-gray-900">{value ?? "-"}</div>
                        {subtext && (
                            <div className="flex items-center gap-1 mt-1">
                                {trend === "negative" && <TrendingDown className="h-3 w-3 text-red-500" />}
                                {trend === "positive" && <TrendingUp className="h-3 w-3 text-green-500" />}
                                {trend === "neutral" && <Minus className="h-3 w-3 text-gray-400" />}

                                <p className={cn(
                                    "text-xs font-medium",
                                    trend === 'negative' ? 'text-red-500' :
                                        trend === 'positive' ? 'text-green-600' :
                                            'text-gray-500'
                                )}>
                                    {subtext}
                                </p>
                            </div>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );

    if (href) return <Link href={href}>{Content}</Link>;
    return Content;
}
