"use client";

import Link from "next/link";
import {
  Bot,
  BarChart3,
  UploadCloud,
  Sparkles,
  ArrowRight,
  Zap,
  Lock,
  ShieldCheck,
  Linkedin,
  Github,
  Mail,
  Cpu,
} from "lucide-react";

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-black text-[#f5f5f7] flex flex-col justify-between selection:bg-cyan-500 selection:text-white font-sans relative overflow-hidden">
      {/* Subtle Apple-style Ambient Gradient Orbs */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-gradient-to-b from-cyan-500/10 via-purple-600/5 to-transparent rounded-full blur-[120px]" />
        <div className="absolute top-1/2 -right-40 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[140px]" />
      </div>

      {/* Header / Apple Frosted Navigation */}
      <header className="border-b border-white/[0.08] backdrop-blur-2xl bg-black/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-500 to-purple-600 shadow-xl shadow-cyan-500/20 ring-1 ring-white/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight text-white">
                Analyst<span className="text-cyan-400">AI</span>
              </span>
              <span className="ml-2 text-[10px] px-2.5 py-0.5 rounded-full bg-white/10 text-slate-300 font-semibold border border-white/15">
                Pro
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/dashboard/upload"
              className="px-5 py-2.5 text-xs font-semibold rounded-full bg-white/10 hover:bg-white/20 text-white transition-all duration-200 border border-white/15 backdrop-blur-md flex items-center space-x-2 shadow-lg"
            >
              <UploadCloud className="w-4 h-4 text-cyan-400" />
              <span>Upload Dataset</span>
            </Link>

            <Link
              href="/dashboard"
              className="px-6 py-2.5 text-xs font-semibold rounded-full bg-white text-black hover:bg-slate-200 transition-all duration-200 shadow-xl flex items-center space-x-2"
            >
              <span>Launch Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Hero & Content */}
      <main className="flex-1 z-10">
        
        {/* Apple Style Hero Section */}
        <section className="pt-24 pb-20 px-6 max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-white/[0.06] border border-white/10 text-cyan-400 text-xs font-semibold tracking-wide mb-8 backdrop-blur-xl">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Autonomous Multi-Agent Data Intelligence</span>
          </div>

          <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white max-w-5xl mx-auto leading-[1.08]">
            Intelligence for your data. <br />
            <span className="bg-gradient-to-r from-white via-[#86868b] to-[#6e6e73] bg-clip-text text-transparent">
              Speed for your decisions.
            </span>
          </h1>

          <p className="mt-8 text-lg sm:text-xl text-[#86868b] max-w-3xl mx-auto font-normal leading-relaxed">
            AnalystAI deploys a team of 4 specialized AI agents working together to clean, analyze, visualize, and summarize your spreadsheets into decision-ready executive reports in under 30 seconds.
          </p>

          <div className="mt-12 flex flex-col sm:flex-row justify-center items-center gap-4">
            <Link
              href="/dashboard/upload"
              className="w-full sm:w-auto px-9 py-4 text-sm font-semibold rounded-full bg-white text-black hover:bg-slate-100 transition-all duration-300 shadow-2xl flex items-center justify-center space-x-3 group"
            >
              <UploadCloud className="w-5 h-5 text-black group-hover:scale-110 transition" />
              <span>Upload Dataset Directly</span>
              <ArrowRight className="w-4 h-4 text-black group-hover:translate-x-1 transition" />
            </Link>
            <a
              href="http://localhost:8000/api/sample-csv"
              download="sample_dataset.csv"
              className="w-full sm:w-auto px-8 py-4 text-sm font-semibold rounded-full bg-white/[0.06] hover:bg-white/10 text-white border border-white/15 transition-all duration-300 backdrop-blur-xl flex items-center justify-center space-x-2"
            >
              <span>Download Sample CSV</span>
            </a>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl text-center">
              <p className="text-3xl font-extrabold text-white">100%</p>
              <p className="text-xs text-[#86868b] mt-1 font-medium">Deterministic & Verified</p>
            </div>
            <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl text-center">
              <p className="text-3xl font-extrabold text-cyan-400">300 DPI</p>
              <p className="text-xs text-[#86868b] mt-1 font-medium">Ultra HD Graphics</p>
            </div>
            <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl text-center">
              <p className="text-3xl font-extrabold text-purple-400">&lt; 30s</p>
              <p className="text-xs text-[#86868b] mt-1 font-medium">Full Pipeline Execution</p>
            </div>
            <div className="p-6 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl text-center">
              <p className="text-3xl font-extrabold text-emerald-400">70B</p>
              <p className="text-xs text-[#86868b] mt-1 font-medium">Groq Llama 3 Intelligence</p>
            </div>
          </div>
        </section>

        {/* What It Does Section */}
        <section className="py-24 border-t border-white/[0.08] bg-gradient-to-b from-black to-[#050507]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-3xl mx-auto mb-20">
              <h2 className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">System Architecture</h2>
              <h3 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">What It Does</h3>
              <p className="text-[#86868b] mt-4 text-base leading-relaxed">
                Rather than relying on a single prone LLM, AnalystAI runs a 4-stage sequential agent pipeline where each agent has strict responsibilities.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              {/* Agent 1 */}
              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl hover:border-white/20 transition-all duration-300 space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center font-bold text-lg">
                  01
                </div>
                <h4 className="text-xl font-bold text-white">Data Cleaner</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Normalizes headers to <code className="text-red-400">snake_case</code>, removes duplicate rows, imputes missing values using median/mode, and strips CSV formula injection threats.
                </p>
              </div>

              {/* Agent 2 */}
              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl hover:border-white/20 transition-all duration-300 space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-lg">
                  02
                </div>
                <h4 className="text-xl font-bold text-white">Analyst Agent</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Computes Pearson correlations, identifies high-variance categories, and detects time-series trends using statistical functions combined with Groq Llama 3 70B reasoning.
                </p>
              </div>

              {/* Agent 3 */}
              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl hover:border-white/20 transition-all duration-300 space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-lg">
                  03
                </div>
                <h4 className="text-xl font-bold text-white">Visualizer Agent</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Generates publication-quality 300 DPI dark neon graphics including bar callouts, gradient line fills, scatter plots, and donut charts.
                </p>
              </div>

              {/* Agent 4 */}
              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl hover:border-white/20 transition-all duration-300 space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg">
                  04
                </div>
                <h4 className="text-xl font-bold text-white">Explainer Agent</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Translates numbers into executive Markdown: <strong>Overview → Key Insights → Actionable CEO Takeaways</strong> formatted for direct presentation.
                </p>
              </div>

            </div>
          </div>
        </section>

        {/* Why You Should Use It Section */}
        <section className="py-24 border-t border-white/[0.08] bg-[#050507]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center max-w-3xl mx-auto mb-20">
              <h2 className="text-xs font-semibold text-purple-400 uppercase tracking-widest mb-3">Value Proposition</h2>
              <h3 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">Why You Should Use It</h3>
              <p className="text-[#86868b] mt-4 text-base leading-relaxed">
                Designed for founders, executives, data teams, and business analysts who need reliable answers without waiting days.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl space-y-4">
                <div className="p-3 rounded-2xl bg-cyan-500/10 text-cyan-400 w-fit">
                  <Zap className="w-6 h-6" />
                </div>
                <h4 className="text-xl font-bold text-white">120x Speed Increase</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Instead of spending hours writing Pandas scripts, creating Matplotlib plots, and drafting summaries, upload your spreadsheet and receive a full report in seconds.
                </p>
              </div>

              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl space-y-4">
                <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400 w-fit">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h4 className="text-xl font-bold text-white">Zero Metric Hallucinations</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Every statistic and trend is computed using deterministic Python mathematical engines. The LLM only interprets verified evidence without inventing numbers.
                </p>
              </div>

              <div className="p-8 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl space-y-4">
                <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 w-fit">
                  <Lock className="w-6 h-6" />
                </div>
                <h4 className="text-xl font-bold text-white">Enterprise Hardened Security</h4>
                <p className="text-xs text-[#86868b] leading-relaxed">
                  Includes MIME type validation, path-traversal filename protection, formula injection stripping, and CORS security.
                </p>
              </div>

            </div>
          </div>
        </section>

        {/* Creator / Founder Engineering Showcase (Without Picture) */}
        <section className="py-24 border-t border-white/[0.08] bg-black">
          <div className="max-w-4xl mx-auto px-6">
            <div className="p-10 sm:p-12 rounded-3xl bg-gradient-to-b from-white/[0.05] to-white/[0.02] border border-white/10 backdrop-blur-2xl text-center space-y-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

              <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/15 text-xs font-semibold text-slate-200">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span>Engineered By Abhishek Chandra</span>
              </div>

              <div>
                <h3 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                  Abhishek Chandra
                </h3>
                <p className="text-sm text-cyan-400 font-semibold mt-1">Full-Stack & Autonomous AI Systems Engineer</p>
                <p className="text-xs text-[#86868b] max-w-xl mx-auto mt-3 leading-relaxed">
                  Architect of the AnalystAI multi-agent engine. Connect via LinkedIn, check out open-source repositories on GitHub, or send an email.
                </p>
              </div>

              {/* Verified Contact Badges (No Picture) */}
              <div className="flex flex-wrap justify-center items-center gap-4 pt-2">
                <a
                  href="https://www.linkedin.com/in/abhishekchandra-sde"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-semibold flex items-center space-x-2.5 transition-all duration-200 backdrop-blur-xl shadow-lg"
                >
                  <svg className="w-4 h-4 text-[#0a66c2] fill-current" viewBox="0 0 24 24">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.25V10.9H6.46M7.86 6.72a1.47 1.47 0 1 0 0 2.94 1.47 1.47 0 0 0 0-2.94Z" />
                  </svg>
                  <span>LinkedIn Profile</span>
                </a>

                <a
                  href="https://www.github.com/ABHI3450"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-semibold flex items-center space-x-2.5 transition-all duration-200 backdrop-blur-xl shadow-lg"
                >
                  <svg className="w-4 h-4 text-slate-200 fill-current" viewBox="0 0 24 24">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>GitHub Repositories</span>
                </a>

                <a
                  href="mailto:abhishek.chandra.dev1@gmail.com"
                  className="px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-semibold flex items-center space-x-2.5 transition-all duration-200 backdrop-blur-xl shadow-lg"
                >
                  <Mail className="w-4 h-4 text-emerald-400" />
                  <span>abhishek.chandra.dev1@gmail.com</span>
                </a>
              </div>
            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.08] py-10 bg-black text-[#86868b] text-xs text-center z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
          <p>© 2026 AnalystAI Platform. Created by Abhishek Chandra.</p>
          <div className="flex space-x-6">
            <Link href="/dashboard" className="hover:text-white transition">Workspace</Link>
            <Link href="/dashboard/upload" className="hover:text-white transition">Upload Dataset</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
