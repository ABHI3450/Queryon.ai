"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, UploadCloud, History, LayoutDashboard, Sparkles, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview Workspace", href: "/dashboard", icon: LayoutDashboard },
  { name: "Upload Dataset", href: "/dashboard/upload", icon: UploadCloud },
  { name: "Report Archives", href: "/dashboard/reports", icon: History },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useUser();

  return (
    <div className="glass-container min-h-screen text-slate-100 flex flex-col md:flex-row relative overflow-hidden font-sans">
      {/* Hyper-Aesthetic Ambient Mesh Orbs */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="mesh-orb-cyan" />
        <div className="mesh-orb-purple" />
        <div className="mesh-orb-pink" />
      </div>

      {/* Frosted Glass Sidebar v2 */}
      <aside className="w-full md:w-72 glass-sidebar-v2 z-20 flex flex-col justify-between shrink-0">
        <div>
          {/* Top-Left Brand Logo - Clicking navigates to Welcome Page (/) */}
          <Link
            href="/"
            className="h-24 px-6 flex items-center space-x-3.5 border-b border-white/10 hover:bg-white/[0.04] transition-all duration-300 cursor-pointer group"
          >
            <div className="p-3 rounded-2xl bg-gradient-to-tr from-cyan-400 via-purple-500 to-pink-500 p-[1.5px] shadow-xl shadow-cyan-500/25 group-hover:scale-110 transition duration-300">
              <div className="w-9 h-9 rounded-[14px] bg-[#030712] flex items-center justify-center">
                <Bot className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-xl tracking-tight text-white group-hover:text-cyan-300 transition">
                  Queryon<span className="text-cyan-400">.ai</span>
                </span>
              </div>
              <div className="flex items-center space-x-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] text-cyan-300 font-bold uppercase tracking-wider">
                  Glassmorphism 3.0
                </span>
              </div>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="p-5 space-y-2.5">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-3.5 px-4 py-3.5 rounded-2xl text-xs font-bold transition-all duration-300 glass-nav-item",
                    isActive
                      ? "glass-nav-item-active text-cyan-300 shadow-xl"
                      : "text-slate-400 hover:text-white hover:bg-white/[0.06] hover:translate-x-1"
                  )}
                >
                  <Icon className={cn("w-4 h-4", isActive ? "text-cyan-400" : "text-slate-400")} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Account Footer */}
        <div className="p-4 m-5 rounded-3xl glass-card-glow flex items-center justify-between border border-white/15">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 flex items-center justify-center font-bold text-xs shrink-0">
              Q
            </div>
            <div className="truncate text-xs">
              <p className="font-bold text-white truncate">{user?.fullName || "User Account"}</p>
              <p className="text-cyan-400 text-[11px] font-semibold truncate">{user?.primaryEmailAddress?.emailAddress || "Free Tier (10/mo)"}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Workspace */}
      <main className="flex-1 overflow-y-auto p-6 md:p-12 z-10">
        <div className="max-w-6xl mx-auto">{children}</div>
      </main>
    </div>
  );
}
