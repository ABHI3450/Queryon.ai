const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface JobStatus {
  job_id: string;
  status: "pending" | "cleaning" | "analyzing" | "visualizing" | "explaining" | "completed" | "failed";
  current_agent: string;
  progress_pct: number;
  message: string;
  error?: string | null;
}

export interface Finding {
  id: string;
  title: string;
  description: string;
  importance: "high" | "medium";
  evidence: Record<string, any>;
  chart_type: string;
}

export interface ChartInfo {
  finding_id: string;
  chart_type: string;
  file_path: string;
  title: string;
}

export interface ReportData {
  job_id: string;
  success: boolean;
  cleaning_summary: {
    rows_before?: number;
    rows_after?: number;
    columns?: string[];
    duplicates_removed?: number;
    missing_values_action?: Record<string, string>;
    issues?: string[];
  };
  findings: Finding[];
  charts: ChartInfo[];
  report_markdown: string;
  report_sections: {
    overview?: string;
    key_insights?: Array<{ title: string; body: string; chart_path?: string }>;
    what_this_means?: string;
  };
  agent_durations?: Record<string, number>;
  total_duration_seconds?: number;
  error?: string | null;
}

export async function uploadFile(file: File, token?: string | null): Promise<{ job_id: string; filename: string; upload_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/api/uploads`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(errorData.detail || "Upload failed");
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/status`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return response.json();
}

export async function getReport(jobId: string): Promise<ReportData> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${jobId}`);
  if (response.status === 202) {
    throw new Error("Report not ready yet");
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Report not found" }));
    throw new Error(err.detail || "Failed to fetch report");
  }
  const data = await response.json();
  if (data && data.success === false) {
    throw new Error(data.error || "Report generation failed");
  }
  return data;
}

export async function getReportsList(): Promise<Array<{ job_id: string; filename: string; status: string; findings_count: number; total_duration_seconds: number }>> {
  const response = await fetch(`${API_BASE_URL}/api/reports`);
  if (!response.ok) {
    throw new Error("Failed to list reports");
  }
  const data = await response.json();
  return data.reports || [];
}

export function getChartImageUrl(jobId: string, chartPath: string): string {
  const filename = chartPath.split(/[\/\\]/).pop();
  return `${API_BASE_URL}/api/reports/${jobId}/charts/${filename}`;
}
