import type {
  Application,
  ApplicationStatus,
  Bookmark,
  Company,
  Job,
  JobListResponse,
  Stats,
} from "./types";

// NEXT_PUBLIC_API_URL is baked in at build time (standard Next.js behavior) and,
// when set, makes the browser call the backend directly - used by docker-compose
// and local dev. When unset, requests go out as same-origin relative paths and are
// proxied server-side by the rewrite in next.config.mjs (BACKEND_INTERNAL_URL,
// read at runtime) - used on hosts where a build-time backend URL isn't available.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface JobFilters {
  search?: string;
  company?: string[];
  role?: string[];
  location?: string;
  india_only?: boolean;
  include_remote?: boolean;
  include_internships?: boolean;
  sort_by?: "rank_score" | "posted_date" | "first_seen_at" | "title";
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

function buildQuery(filters: JobFilters): string {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  filters.company?.forEach((c) => params.append("company", c));
  filters.role?.forEach((r) => params.append("role", r));
  if (filters.location) params.set("location", filters.location);
  if (filters.india_only !== undefined) params.set("india_only", String(filters.india_only));
  if (filters.include_remote !== undefined) params.set("include_remote", String(filters.include_remote));
  if (filters.include_internships !== undefined)
    params.set("include_internships", String(filters.include_internships));
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.order) params.set("order", filters.order);
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));
  if (filters.offset !== undefined) params.set("offset", String(filters.offset));
  return params.toString();
}

export const api = {
  listJobs: (filters: JobFilters = {}) => request<JobListResponse>(`/api/jobs?${buildQuery(filters)}`),
  getJob: (id: string) => request<Job>(`/api/jobs/${id}`),
  triggerScrape: () => request<{ companies_scraped: number; jobs_found: number; new_jobs: number }>(
    `/api/jobs/scrape-now`,
    { method: "POST" }
  ),
  listCompanies: () => request<Company[]>(`/api/companies`),
  getStats: () => request<Stats>(`/api/stats`),

  listBookmarks: () => request<Bookmark[]>(`/api/bookmarks`),
  addBookmark: (job_id: string, note = "") =>
    request<Bookmark>(`/api/bookmarks`, { method: "POST", body: JSON.stringify({ job_id, note }) }),
  removeBookmark: (id: string) => request<void>(`/api/bookmarks/${id}`, { method: "DELETE" }),

  listApplications: () => request<Application[]>(`/api/applications`),
  addApplication: (job_id: string, status: ApplicationStatus = "saved") =>
    request<Application>(`/api/applications`, { method: "POST", body: JSON.stringify({ job_id, status }) }),
  updateApplication: (id: string, patch: Partial<Pick<Application, "status" | "notes">>) =>
    request<Application>(`/api/applications/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  removeApplication: (id: string) => request<void>(`/api/applications/${id}`, { method: "DELETE" }),

  exportUrl: (format: "csv" | "xlsx") => `${API_BASE}/api/export/${format}`,
};
