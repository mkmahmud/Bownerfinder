export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend/api/v1";
const FRONTEND_BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://127.0.0.1:3000";

export type Job = {
  id: string;
  status: string;
  source_filename: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type JobStats = {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  companies_total: number;
  companies_enriched: number;
};

export type UploadError = {
  row_number: number;
  message: string;
};

export type UploadResponse = {
  job: Job;
  errors: UploadError[];
};

export type Company = {
  id: string;
  job_id: string;
  row_number: number;
  business_name: string;
  normalized_business_name: string;
  website: string | null;
  phone: string | null;
  email: string | null;
  linkedin: string | null;
  facebook: string | null;
  instagram: string | null;
  decision_maker_name: string | null;
  decision_maker_title: string | null;
  confidence_score: number | null;
  validation_errors: string | null;
  created_at: string;
  updated_at: string;
};

export type ResultRow = Company & {
  enrichment_status: string;
  evidence_count: number;
  contact_count: number;
};

export type ResultListResponse = {
  items: ResultRow[];
  total: number;
};

export type ExportRecord = {
  id: string;
  job_id: string;
  format: string;
  status: string;
  file_path: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type EnrichmentRequest = {
  mode?: string;
};

export type ExportRequest = {
  format?: "csv" | "xlsx";
  selected_company_ids?: string[] | null;
  job_id?: string | null;
};

function buildApiUrl(path: string): string {
  const apiPath = `${API_BASE_URL}${path}`;
  if (typeof window !== "undefined") {
    return apiPath;
  }
  return new URL(apiPath, FRONTEND_BASE_URL).toString();
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Unable to reach the local backend. Start the FastAPI server on port 8000, then retry.");
    }
    throw error;
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function uploadLeads(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<UploadResponse>("/uploads", {
    method: "POST",
    body: formData,
  });
}

export async function listJobs(): Promise<Job[]> {
  return request<Job[]>("/jobs");
}

export async function listCompanies(jobId: string): Promise<Company[]> {
  return request<Company[]>(`/jobs/${jobId}/companies`);
}

export async function getJobStats(): Promise<JobStats> {
  return request<JobStats>("/results/stats");
}

export async function listResults(params?: { query?: string; jobId?: string; status?: string; minConfidence?: number; sort?: string }): Promise<ResultRow[]> {
  const searchParams = new URLSearchParams();
  if (params?.query) searchParams.set("query", params.query);
  if (params?.jobId) searchParams.set("job_id", params.jobId);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.minConfidence !== undefined) searchParams.set("min_confidence", String(params.minConfidence));
  if (params?.sort) searchParams.set("sort", params.sort);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const response = await request<ResultListResponse>(`/results${suffix}`);
  return response.items;
}

export async function triggerEnrichment(jobId: string, payload: EnrichmentRequest = {}): Promise<Job> {
  return request<Job>(`/jobs/${jobId}/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function createExport(jobId: string, payload: ExportRequest): Promise<ExportRecord> {
  const response = await request<{ export: ExportRecord }>(`/exports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, job_id: payload.job_id ?? jobId }),
  });
  return response.export;
}

export async function listExports(jobId?: string): Promise<ExportRecord[]> {
  const suffix = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
  return request<ExportRecord[]>(`/exports${suffix}`);
}

export function getExportDownloadUrl(exportId: string): string {
  return `${API_BASE_URL}/exports/${exportId}/download`;
}

