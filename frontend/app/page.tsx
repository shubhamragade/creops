import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, ShieldCheck, Zap, BarChart3, Clock } from "lucide-react";

export default function Home() {
    return (
        <div className="flex flex-col min-h-screen bg-white">
            {/* Navigation */}
            <header className="px-4 lg:px-6 h-16 flex items-center border-b shadow-sm sticky top-0 bg-white/80 backdrop-blur-md z-50">
                <Link className="flex items-center justify-center" href="#">
                    <ShieldCheck className="h-6 w-6 text-indigo-600" />
                    <span className="ml-2 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-indigo-400">CareOps</span>
                </Link>
                <nav className="ml-auto flex gap-4 sm:gap-6 items-center">
                    <Link className="text-sm font-medium hover:underline underline-offset-4" href="#features">
                        Features
                    </Link>
                    <Link href="/login">
                        <Button variant="ghost" size="sm">Login</Button>
                    </Link>
                    <Link href="/signup">
                        <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700">Get Started</Button>
                    </Link>
                </nav>
            </header>

            <main className="flex-1">
                {/* Hero Section */}
                <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48 bg-gradient-to-b from-indigo-50 to-white">
                    <div className="container px-4 md:px-6 mx-auto">
                        <div className="flex flex-col items-center space-y-4 text-center">
                            <div className="space-y-2">
                                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
                                    The Operating System for <br />
                                    <span className="text-indigo-600">Care Businesses</span>
                                </h1>
                                <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400 mt-4">
                                    Automate bookings, manage inventory, and handle customer communication in one secure, unified platform. Built for trust and resilience.
                                </p>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-4 mt-8">
                                <Link href="/signup">
                                    <Button size="lg" className="bg-indigo-600 hover:bg-indigo-700 h-12 px-8 text-lg">
                                        Start Your Workspace <ArrowRight className="ml-2 h-5 w-5" />
                                    </Button>
                                </Link>
                                <Link href="/book/demo-spa">
                                    <Button variant="outline" size="lg" className="h-12 px-8 text-lg">
                                        View Public Booking
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Integration Proof Section */}
                <section id="features" className="w-full py-12 md:py-24 lg:py-32">
                    <div className="container px-4 md:px-6 mx-auto">
                        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
                            <div className="flex flex-col items-center space-y-2 border p-6 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                                <Zap className="h-10 w-10 text-indigo-600 mb-2" />
                                <h3 className="text-xl font-bold">Automated Resilience</h3>
                                <p className="text-sm text-gray-500 text-center">
                                    Self-healing bookings that detect failures and offer instant restoration options.
                                </p>
                            </div>
                            <div className="flex flex-col items-center space-y-2 border p-6 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                                <BarChart3 className="h-10 w-10 text-indigo-600 mb-2" />
                                <h3 className="text-xl font-bold">Live Ops Dashboard</h3>
                                <p className="text-sm text-gray-500 text-center">
                                    Real-time signals for inventory, failed communications, and pending intake forms.
                                </p>
                            </div>
                            <div className="flex flex-col items-center space-y-2 border p-6 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                                <Clock className="h-10 w-10 text-indigo-600 mb-2" />
                                <h3 className="text-xl font-bold">Smart Scheduling</h3>
                                <p className="text-sm text-gray-500 text-center">
                                    Capacity-aware booking flow that handles timezones and inventory constraints.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="flex flex-col gap-2 sm:flex-row py-6 w-full shrink-0 items-center px-4 md:px-6 border-t font-medium text-sm text-gray-500">
                <p>© 2026 CareOps Platform. All rights reserved.</p>
                <nav className="sm:ml-auto flex gap-4 sm:gap-6">
                    <Link className="hover:underline underline-offset-4" href="#">Terms of Service</Link>
                    <Link className="hover:underline underline-offset-4" href="#">Privacy</Link>
                </nav>
            </footer>
        </div>
    );
}
