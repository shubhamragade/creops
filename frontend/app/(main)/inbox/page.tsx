"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast-context";
import {
    Send,
    Clock,
    User as UserIcon,
    ArrowLeft,
    CheckCircle2,
    Search,
    MessageSquare
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
    id: number;
    content: string;
    sender_email: string;
    is_internal: boolean;
    created_at: string;
}

interface Conversation {
    id: number;
    subject: string;
    last_message_at: string;
    is_paused: boolean;
    unanswered: boolean;
    contact_id: number;
    contact_email?: string; // If available from API
}

export default function InboxPage() {
    const router = useRouter();
    const { showToast } = useToast();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [replyContent, setReplyContent] = useState("");
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);

    // Auto-scroll ref
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        fetchConversations();
    }, []);

    useEffect(() => {
        if (selectedId) {
            fetchMessages(selectedId);
        }
    }, [selectedId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchConversations = async () => {
        try {
            const res = await api.get("/api/conversations");
            setConversations(res.data);
            setLoading(false);
        } catch (error) {
            console.error(error);
            showToast("Failed to load conversations", "error");
        }
    };

    const fetchMessages = async (id: number) => {
        try {
            const res = await api.get(`/api/conversations/${id}`);
            setMessages(res.data);
        } catch (error) {
            console.error(error);
            showToast("Failed to load messages", "error");
        }
    };

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!replyContent.trim() || !selectedId) return;

        setSending(true);
        try {
            await api.post(`/api/conversations/messages`, {
                conversation_id: selectedId,
                content: replyContent,
            });
            setReplyContent("");
            showToast("Reply sent via Gmail", "success");
            // Refresh messages and conversation list (to update status)
            await fetchMessages(selectedId);
            await fetchConversations();
        } catch (error) {
            console.error("Failed to send", error);
            showToast("Failed to send reply. Check Gmail connection.", "error");
        } finally {
            setSending(false);
        }
    };

    const selectedConversation = conversations.find((c) => c.id === selectedId);

    return (
        <div className="flex h-screen bg-white overflow-hidden">
            {/* Sidebar List */}
            <div className="w-1/3 min-w-[320px] max-w-[400px] border-r border-gray-200 flex flex-col bg-gray-50/50">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-white sticky top-0 z-10">
                    <h1 className="font-bold text-xl text-gray-900 tracking-tight">Inbox</h1>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="icon" onClick={async () => {
                            setLoading(true);
                            try {
                                await api.post("/api/inbox/sync");
                                await fetchConversations();
                                showToast("Inbox Synced", "success");
                            } catch (e) {
                                showToast("Sync failed", "error");
                            } finally {
                                setLoading(false);
                            }
                        }} title="Refresh Inbox">
                            <Clock className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => {
                            const role = localStorage.getItem("user_role");
                            if (role === "staff") {
                                router.push("/staff");
                            } else {
                                router.push("/dashboard");
                            }
                        }} className="text-gray-500 hover:text-gray-900">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back
                        </Button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="p-4 space-y-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="flex gap-3">
                                    <Skeleton className="h-10 w-10 rounded-full" />
                                    <div className="space-y-2 flex-1">
                                        <Skeleton className="h-4 w-3/4" />
                                        <Skeleton className="h-3 w-1/2" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="p-8 text-center text-gray-500 flex flex-col items-center">
                            <MessageSquare className="h-10 w-10 text-gray-300 mb-2" />
                            <p>No conversations yet.</p>
                        </div>
                    ) : (
                        conversations.map((conv) => (
                            <div
                                key={conv.id}
                                onClick={() => setSelectedId(conv.id)}
                                className={cn(
                                    "p-4 border-b border-gray-100 cursor-pointer transition-all duration-200 hover:bg-gray-100",
                                    selectedId === conv.id ? "bg-white border-l-4 border-l-indigo-600 shadow-sm" : "border-l-4 border-l-transparent bg-white/50"
                                )}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className={cn(
                                        "font-medium truncate pr-2 text-sm",
                                        conv.unanswered ? "text-gray-900 font-bold" : "text-gray-700"
                                    )}>
                                        {conv.subject || "No Subject"}
                                    </span>
                                    {conv.last_message_at && (
                                        <span className="text-[10px] text-gray-400 whitespace-nowrap">
                                            {formatDate(conv.last_message_at)}
                                        </span>
                                    )}
                                </div>

                                <div className="flex items-center gap-2 mt-2">
                                    {conv.unanswered && (
                                        <Badge variant="warning" className="text-[10px] px-1.5 py-0 rounded-md">Unanswered</Badge>
                                    )}
                                    {conv.is_paused && (
                                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 flex items-center gap-1 rounded-md text-gray-500 bg-gray-100">
                                            <Clock className="w-3 h-3" /> Paused
                                        </Badge>
                                    )}
                                    <span className="text-[10px] text-gray-400 ml-auto font-mono">
                                        #{conv.id}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col bg-white relative">
                {selectedId && selectedConversation ? (
                    <>
                        {/* Header */}
                        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white shadow-sm z-10">
                            <div className="flex flex-col">
                                <h2 className="font-bold text-lg text-gray-900">{selectedConversation.subject}</h2>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <span>Conversation #{selectedId}</span>
                                    {selectedConversation.contact_email && (
                                        <>
                                            <span>•</span>
                                            <span>{selectedConversation.contact_email}</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            {selectedConversation.is_paused && (
                                <div className="flex items-center gap-2 bg-amber-50 text-amber-700 px-3 py-1.5 rounded-full text-xs font-medium border border-amber-200">
                                    <Clock className="w-3 h-3" />
                                    Automation Paused
                                </div>
                            )}
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30">
                            {messages.length === 0 && (
                                <div className="text-center text-gray-400 mt-10">
                                    <p>No messages in this conversation yet.</p>
                                </div>
                            )}

                            {messages.map((msg) => {
                                const isMe = msg.is_internal;
                                return (
                                    <div
                                        key={msg.id}
                                        className={`flex ${isMe ? "justify-end" : "justify-start"}`}
                                    >
                                        <div className={cn(
                                            "max-w-[70%] rounded-2xl p-4 shadow-sm text-sm leading-relaxed",
                                            isMe
                                                ? "bg-indigo-600 text-white rounded-br-sm"
                                                : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm"
                                        )}>
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                            <div className={cn(
                                                "mt-1.5 flex items-center justify-end text-[10px] uppercase tracking-wide opacity-70",
                                                isMe ? "text-indigo-100" : "text-gray-400"
                                            )}>
                                                <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="p-4 border-t border-gray-200 bg-white">
                            {selectedConversation.is_paused && (
                                <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-green-50 text-green-700 rounded-md text-xs border border-green-100">
                                    <CheckCircle2 className="w-4 h-4" />
                                    <span className="font-medium">Replying will resume automation automatically.</span>
                                </div>
                            )}
                            <form onSubmit={handleSend} className="flex gap-3 items-end">
                                <div className="flex-1 relative">
                                    <textarea
                                        value={replyContent}
                                        onChange={(e) => setReplyContent(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                handleSend(e);
                                            }
                                        }}
                                        placeholder="Type your reply... (Enter to send)"
                                        className="flex-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-3 text-sm ring-offset-background placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none min-h-[50px] max-h-[150px]"
                                        disabled={sending}
                                        autoFocus
                                        rows={1}
                                    />
                                    <div className="absolute bottom-3 right-3 text-[10px] text-gray-400">
                                        Press Shift + Enter for new line
                                    </div>
                                </div>
                                <Button
                                    type="submit"
                                    disabled={sending || !replyContent.trim()}
                                    className="h-[50px] w-[50px] rounded-lg p-0 flex items-center justify-center bg-indigo-600 hover:bg-indigo-700"
                                >
                                    {sending ? <Spinner className="w-5 h-5 text-white" /> : <Send className="w-5 h-5 text-white" />}
                                </Button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50/30">
                        <div className="h-20 w-20 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                            <MessageSquare className="w-10 h-10 text-gray-300" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900">Select a conversation</h3>
                        <p className="max-w-xs text-center mt-2 text-sm text-gray-500">Choose a conversation from the sidebar to view messages and reply.</p>
                    </div>
                )}
            </div>
        </div>
    );
}

function formatDate(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString();
}
