"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { UploadCloud, FileSpreadsheet, Loader2, AlertCircle, Sparkles, ShieldCheck } from "lucide-react";
import { uploadFile } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);

      const token = await getToken();
      const response = await uploadFile(file, token);
      router.push(`/dashboard/reports/${response.job_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to upload file. Please try again.");
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-10">
      <div>
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full glass-badge-cyan text-xs font-bold uppercase tracking-wider mb-4">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>4-Agent Automated Pipeline</span>
        </div>
        <h1 className="text-4xl font-black text-white">Upload Dataset</h1>
        <p className="text-slate-300 text-sm mt-2">Select a CSV or Excel (.xlsx) file to launch the multi-agent analysis pipeline.</p>
      </div>

      {/* Sample Data Glass Notice */}
      <div className="p-6 rounded-3xl glass-card-glow flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 rounded-2xl bg-cyan-500/15 border border-cyan-400/30 text-cyan-400 shrink-0">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Need realistic sample data to test?</p>
            <p className="text-xs text-slate-300 mt-0.5">Download dataset containing sample sales metrics with missing values & outliers.</p>
          </div>
        </div>
        <a
          href="http://localhost:8000/api/sample-csv"
          download="sample_dataset.csv"
          className="px-5 py-2.5 rounded-2xl glass-btn-neon text-xs font-bold shrink-0 transition"
        >
          Download Sample CSV
        </a>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Hyper-Glass Drag & Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="relative p-14 rounded-3xl glass-card-glow border-2 border-dashed border-cyan-400/30 hover:border-cyan-400 transition duration-300 text-center flex flex-col items-center justify-center space-y-5 group cursor-pointer"
        >
          <input
            type="file"
            id="fileInput"
            onChange={handleFileChange}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
          />

          <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-cyan-500/20 via-purple-500/20 to-pink-500/20 border border-cyan-400/40 text-cyan-300 flex items-center justify-center group-hover:scale-110 transition duration-300 shadow-2xl shadow-cyan-500/20">
            <UploadCloud className="w-10 h-10" />
          </div>

          <div>
            {file ? (
              <div className="space-y-1">
                <p className="font-extrabold text-cyan-300 text-lg">{file.name}</p>
                <p className="text-xs text-slate-300">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            ) : (
              <>
                <p className="font-extrabold text-white text-lg">Drag & drop your dataset here, or <span className="text-cyan-400 underline decoration-cyan-400/50 underline-offset-4">browse</span></p>
                <p className="text-xs text-slate-400 mt-1.5">Supports CSV, XLSX, XLS up to 25 MB</p>
              </>
            )}
          </div>
        </div>

        {/* Security & Validation Notice */}
        <div className="flex items-center space-x-2 text-xs text-slate-300 px-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>MIME type validated, formula sanitized, encrypted in transit</span>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-5 rounded-2xl bg-red-500/15 border border-red-500/30 text-red-200 text-xs flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Glowing Launch Button */}
        <button
          type="submit"
          disabled={!file || isUploading}
          className="w-full py-4 rounded-2xl glass-btn-neon flex items-center justify-center space-x-2.5 text-sm font-extrabold disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-white" />
              <span>Launching AI Agent Pipeline...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 text-white" />
              <span>Start Multi-Agent Analysis</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
