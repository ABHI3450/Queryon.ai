"use client";

import Link from "next/link";
import { UploadCloud, History, ArrowRight, Cpu, Sparkles, ShieldCheck, Zap, Activity } from "lucide-react";

export default function DashboardHome() {
  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full glass-badge-cyan text-xs font-bold uppercase tracking-wider mb-4">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>Enterprise Autonomous AI Workspace</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white">
          Data Analyst <span className="text-shimmer-neon">Command Workspace</span>
        </h1>
        <p className="text-slate-300 text-sm sm:text-base mt-2 max-w-2xl font-normal leading-relaxed">
          Upload raw CSV or Excel spreadsheets. Your 4 autonomous AI agents execute a sequential analytical pipeline—cleaning, statistical correlation mining, 300 DPI neon chart plotting, and executive report writing.
        </p>
      </div>

      {/* Quick Action Glass Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Link
          href="/dashboard/upload"
          className="p-8 rounded-3xl glass-card-glow group flex flex-col justify-between"
        >
          <div>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500/20 via-purple-500/20 to-pink-500/20 border border-cyan-400/40 text-cyan-300 flex items-center justify-center mb-6 group-hover:scale-110 transition duration-300 shadow-xl shadow-cyan-500/20">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-black text-white group-hover:text-cyan-300 transition">Upload New Dataset</h3>
            <p className="text-slate-300 text-xs sm:text-sm mt-3 leading-relaxed">
              Drag and drop any CSV or Excel file (up to 25 MB). Automatic missing value median/mode imputation, IQR outlier detection, and formula threat sanitization included.
            </p>
          </div>
          <div className="mt-8 inline-flex items-center text-xs font-extrabold text-cyan-400 space-x-2 group-hover:translate-x-2 transition duration-300">
            <span>Launch AI Pipeline</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </Link>

        <Link
          href="/dashboard/reports"
          className="p-8 rounded-3xl glass-card-glow group flex flex-col justify-between"
        >
          <div>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-500/20 via-pink-500/20 to-cyan-500/20 border border-purple-400/40 text-purple-300 flex items-center justify-center mb-6 group-hover:scale-110 transition duration-300 shadow-xl shadow-purple-500/20">
              <History className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-black text-white group-hover:text-purple-300 transition">View Past Reports</h3>
            <p className="text-slate-300 text-xs sm:text-sm mt-3 leading-relaxed">
              Browse previously generated executive analysis reports, inspect data quality metrics, view 300 DPI graphics, and export Markdown documents.
            </p>
          </div>
          <div className="mt-8 inline-flex items-center text-xs font-extrabold text-purple-400 space-x-2 group-hover:translate-x-2 transition duration-300">
            <span>Browse Archives</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </Link>
      </div>

      {/* System Status Glass Banner */}
      <div className="p-8 rounded-3xl glass-card-glow flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="flex items-center space-x-5">
          <div className="p-4 rounded-2xl bg-emerald-500/15 border border-emerald-400/30 text-emerald-400 shrink-0 shadow-lg shadow-emerald-500/10">
            <Cpu className="w-7 h-7" />
          </div>
          <div>
            <h4 className="font-extrabold text-white text-base flex items-center space-x-2">
              <span>All 4 Autonomous Agents Operational</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </h4>
            <p className="text-xs text-slate-300 mt-1">Cleaner, Analyst (Groq 70B), Visualizer (300 DPI), Explainer ready.</p>
          </div>
        </div>
        <div className="shrink-0">
          <span className="px-5 py-2 rounded-full glass-badge-emerald text-xs font-bold border">
            Free Tier: 10/10 Remaining
          </span>
        </div>
      </div>
    </div>
  );
}
