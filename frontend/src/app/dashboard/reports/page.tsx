"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { History, FileText, CheckCircle2, Sparkles, ArrowRight } from "lucide-react";
import { getReportsList } from "@/lib/api";

export default function ReportsHistoryPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReportsList()
      .then((data) => {
        setReports(data);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load report history");
        setIsLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full glass-pill text-xs font-semibold text-purple-400 mb-3 border border-purple-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Audit History & Archives</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white">Report History</h1>
          <p className="text-slate-400 text-sm mt-1">Audit log of all previously processed datasets and generated reports.</p>
        </div>

        <Link
          href="/dashboard/upload"
          className="px-5 py-2.5 rounded-2xl glass-btn-primary text-xs font-semibold shadow-lg shadow-cyan-500/20 flex items-center space-x-2 shrink-0"
        >
          <span>+ New Upload</span>
        </Link>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-sm glass-card rounded-3xl">Loading report history...</div>
      ) : error ? (
        <div className="p-6 rounded-3xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">{error}</div>
      ) : reports.length === 0 ? (
        <div className="p-16 text-center rounded-3xl glass-card border border-white/10 space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mx-auto">
            <History className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">No Reports Found</h3>
            <p className="text-slate-400 text-sm mt-1">You haven't uploaded any datasets for multi-agent analysis yet.</p>
          </div>
          <Link
            href="/dashboard/upload"
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-2xl glass-btn-primary text-xs font-semibold"
          >
            <span>Upload Your First Dataset</span>
          </Link>
        </div>
      ) : (
        <div className="rounded-3xl overflow-hidden glass-card border border-white/10 shadow-2xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 text-slate-400 border-b border-white/10">
              <tr>
                <th className="px-6 py-4 font-semibold">Dataset Filename</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold">Insights Found</th>
                <th className="px-6 py-4 font-semibold">Duration</th>
                <th className="px-6 py-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-slate-300">
              {reports.map((report) => (
                <tr key={report.job_id} className="hover:bg-white/5 transition duration-200">
                  <td className="px-6 py-4 font-semibold text-white flex items-center space-x-3">
                    <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <span>{report.filename}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{report.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium">{report.findings_count} insights</td>
                  <td className="px-6 py-4 font-medium text-slate-400">{report.total_duration_seconds}s</td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/dashboard/reports/${report.job_id}`}
                      className="inline-flex items-center space-x-1.5 text-xs font-bold text-cyan-400 hover:text-cyan-300 transition"
                    >
                      <span>View Report</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
