export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

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
  confidence_score: number | null;
  validation_errors: string | null;
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
  });
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

