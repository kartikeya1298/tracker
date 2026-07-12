export type ATSPlatform =
  | "greenhouse"
  | "lever"
  | "workday"
  | "taleo"
  | "successfactors"
  | "oracle_careers"
  | "sap_careers"
  | "custom";

export interface Company {
  id: string;
  name: string;
  slug: string;
  platform: ATSPlatform;
  careers_url: string;
  logo_url: string;
  active: boolean;
}

export interface Job {
  id: string;
  company_id: string;
  title: string;
  normalized_role: string;
  location: string;
  is_india: boolean;
  is_remote: boolean;
  is_internship: boolean;
  experience_required: string;
  min_experience_years: number | null;
  max_experience_years: number | null;
  salary: string;
  description: string;
  skills: string;
  apply_url: string;
  posted_date: string | null;
  ai_summary: string;
  ai_skills: string;
  resume_match_score: number | null;
  resume_match_notes: string;
  learning_recommendations: string;
  rank_score: number | null;
  first_seen_at: string;
  company: Company | null;
}

export interface JobListResponse {
  total: number;
  items: Job[];
}

export interface Stats {
  total_jobs: number;
  jobs_today: number;
  jobs_this_week: number;
  companies_tracked: number;
  companies_with_jobs: number;
  by_company: Record<string, number>;
  by_role: Record<string, number>;
  by_location: Record<string, number>;
  last_scrape_at: string | null;
  last_scrape_new_jobs: number;
}

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "in_progress"
  | "interviewing"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Bookmark {
  id: string;
  job_id: string;
  note: string;
  created_at: string;
  job: Job | null;
}

export interface Application {
  id: string;
  job_id: string;
  status: ApplicationStatus;
  notes: string;
  applied_at: string | null;
  created_at: string;
  updated_at: string;
  job: Job | null;
}
