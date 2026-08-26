"use client";

import { use, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { CheckCircle2, Loader2, AlertCircle, Sparkles, BarChart2, FileText, Download, Clock } from "lucide-react";
import { getReport, getJobStatus, getChartImageUrl, JobStatus } from "@/lib/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SingleReportViewerPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;

  const [status, setStatus] = useState<JobStatus | null>(null);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    const fetchReport = async () => {
      try {
        const data = await getReport(jobId);
        setReport(data);
        if (pollInterval) clearInterval(pollInterval);
        if (eventSource) eventSource.close();
      } catch (err: any) {
        // Report not ready yet or pending
      }
    };

    const fetchStatus = async () => {
      try {
        const st = await getJobStatus(jobId);
        setStatus(st);
        if (st.status === "completed") {
          await fetchReport();
        } else if (st.status === "failed") {
          setError(st.error || st.message || "Job execution failed");
          if (pollInterval) clearInterval(pollInterval);
          if (eventSource) eventSource.close();
        }
      } catch (err) {
        // Ignored
      }
    };

    // Initial check
    fetchReport();
    fetchStatus();

    // Setup polling every 2s
    pollInterval = setInterval(() => {
      if (!report) {
        fetchStatus();
        fetchReport();
      }
    }, 2000);

    // SSE connection
    try {
      eventSource = new EventSource(`${API_BASE_URL}/api/jobs/${jobId}/stream`);

      eventSource.addEventListener("status", (e: MessageEvent) => {
        try {
          const parsedStatus: JobStatus = JSON.parse(e.data);
          setStatus(parsedStatus);
          if (parsedStatus.status === "failed") {
            setError(parsedStatus.error || parsedStatus.message || "Pipeline job failed");
          }
        } catch {}
      });

      eventSource.addEventListener("complete", () => {
        fetchReport();
      });

      eventSource.onerror = () => {
        if (eventSource) eventSource.close();
      };
    } catch {}

    return () => {
      if (pollInterval) clearInterval(pollInterval);
      if (eventSource) eventSource.close();
    };
  }, [jobId]);

  // Download report as markdown text
  const handleDownloadMarkdown = () => {
    if (!report?.report_markdown) return;
    const blob = new Blob([report.report_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${jobId.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Multi-Agent Generated Analysis</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Executive Data Report</h1>
          <p className="text-xs text-slate-400 mt-0.5">Job Reference: {jobId}</p>
        </div>

        {report && (
          <button
            onClick={handleDownloadMarkdown}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-2xl glass-btn-primary text-xs transition shadow-lg shadow-cyan-500/20"
          >
            <Download className="w-4 h-4" />
            <span>Download Report (.md)</span>
          </button>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-6 rounded-3xl bg-red-500/10 border border-red-500/30 backdrop-blur-xl flex items-start space-x-3 text-red-300">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-white">Analysis Failed</h3>
            <p className="text-xs text-red-300 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Real-time SSE Agent Processing Status Bar */}
      {!report && !error && (
        <div className="p-8 rounded-3xl glass-card space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">AI Agents at Work</h3>
                <p className="text-xs text-slate-400 mt-0.5">{status?.message || "Initializing agents pipeline..."}</p>
              </div>
            </div>
            <span className="text-base font-extrabold text-gradient">{status?.progress_pct || 10}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-white/5 rounded-full h-3 overflow-hidden p-[2px] border border-white/10">
            <div
              className="bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 h-full rounded-full transition-all duration-500 shadow-md shadow-cyan-500/50"
              style={{ width: `${status?.progress_pct || 10}%` }}
            />
          </div>

          {/* 4 Agent Badges */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className={`p-4 rounded-2xl border transition ${status?.status === 'cleaning' ? 'glass-pill text-cyan-300 border-cyan-500/40 shadow-lg shadow-cyan-500/10' : 'bg-white/5 border-white/5 text-slate-500'}`}>
              <p className="font-bold">1. Cleaner Agent</p>
              <p className="text-[10px] mt-0.5 opacity-80">Duplicates & Missing</p>
            </div>
            <div className={`p-4 rounded-2xl border transition ${status?.status === 'analyzing' ? 'glass-pill text-purple-300 border-purple-500/40 shadow-lg shadow-purple-500/10' : 'bg-white/5 border-white/5 text-slate-500'}`}>
              <p className="font-bold">2. Analyst Agent</p>
              <p className="text-[10px] mt-0.5 opacity-80">Groq 70B Reasoning</p>
            </div>
            <div className={`p-4 rounded-2xl border transition ${status?.status === 'visualizing' ? 'glass-pill text-pink-300 border-pink-500/40 shadow-lg shadow-pink-500/10' : 'bg-white/5 border-white/5 text-slate-500'}`}>
              <p className="font-bold">3. Visualizer Agent</p>
              <p className="text-[10px] mt-0.5 opacity-80">300 DPI Neon Graphics</p>
            </div>
            <div className={`p-4 rounded-2xl border transition ${status?.status === 'explaining' ? 'glass-pill text-emerald-300 border-emerald-500/40 shadow-lg shadow-emerald-500/10' : 'bg-white/5 border-white/5 text-slate-500'}`}>
              <p className="font-bold">4. Explainer Agent</p>
              <p className="text-[10px] mt-0.5 opacity-80">Markdown Executive Summary</p>
            </div>
          </div>
        </div>
      )}

      {/* Render Generated Report */}
      {report && (
        <div className="space-y-8">
          {/* Cleaning Summary Accordion */}
          {report.cleaning_summary && (
            <div className="p-6 rounded-3xl glass-card space-y-4">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Agent 1: Data Cleaner Summary</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-slate-400">Rows Before</p>
                  <p className="text-xl font-extrabold text-white mt-1">{report.cleaning_summary.rows_before || 0}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-slate-400">Cleaned Rows</p>
                  <p className="text-xl font-extrabold text-emerald-400 mt-1">{report.cleaning_summary.rows_after || 0}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-slate-400">Duplicates Removed</p>
                  <p className="text-xl font-extrabold text-cyan-400 mt-1">{report.cleaning_summary.duplicates_removed || 0}</p>
                </div>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-slate-400">Execution Time</p>
                  <p className="text-xl font-extrabold text-purple-400 mt-1">{report.total_duration_seconds || 0}s</p>
                </div>
              </div>
            </div>
          )}

          {/* Render Generated Charts Grid */}
          {report.charts && report.charts.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <BarChart2 className="w-5 h-5 text-cyan-400" />
                <span>Agent 3: High-DPI Visualizations</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {report.charts.map((chart: any, idx: number) => (
                  <div key={idx} className="p-5 rounded-3xl glass-card space-y-4">
                    <h4 className="font-bold text-sm text-slate-100">{chart.title}</h4>
                    <div className="overflow-hidden rounded-2xl border border-white/10 shadow-2xl">
                      <img
                        src={getChartImageUrl(jobId, chart.file_path)}
                        alt={chart.title}
                        className="w-full h-auto object-cover"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Markdown Plain-English Summary */}
          <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 prose prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-li:text-slate-300">
            <ReactMarkdown>{report.report_markdown}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
