"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type JobFilters } from "@/lib/api";
import type { Application, ApplicationStatus, Bookmark, Company, Job, Stats } from "@/lib/types";
import { StatsCards } from "@/components/StatsCards";
import { FiltersBar } from "@/components/FiltersBar";
import { JobList } from "@/components/JobList";
import { ApplicationTracker } from "@/components/ApplicationTracker";
import { ExportButtons } from "@/components/ExportButtons";
import { DarkModeToggle } from "@/components/DarkModeToggle";

type Tab = "jobs" | "bookmarks" | "applications";

export default function DashboardPage() {
  const [tab, setTab] = useState<Tab>("jobs");
  const [stats, setStats] = useState<Stats | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<JobFilters>({
    include_remote: true,
    include_internships: false,
    sort_by: "rank_score",
    order: "desc",
    limit: 50,
    offset: 0,
  });
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    api.getStats().then(setStats).catch(() => {});
    api.listCompanies().then(setCompanies).catch(() => {});
    refreshBookmarks();
    refreshApplications();
  }, []);

  useEffect(() => {
    setJobsLoading(true);
    api
      .listJobs(filters)
      .then((res) => {
        setJobs(res.items);
        setTotal(res.total);
      })
      .catch(() => {})
      .finally(() => setJobsLoading(false));
  }, [filters]);

  function refreshBookmarks() {
    api.listBookmarks().then(setBookmarks).catch(() => {});
  }
  function refreshApplications() {
    api.listApplications().then(setApplications).catch(() => {});
  }

  const bookmarkedJobIds = useMemo(() => new Set(bookmarks.map((b) => b.job_id)), [bookmarks]);
  const bookmarkByJobId = useMemo(() => new Map(bookmarks.map((b) => [b.job_id, b])), [bookmarks]);

  async function toggleBookmark(jobId: string) {
    const existing = bookmarkByJobId.get(jobId);
    if (existing) {
      await api.removeBookmark(existing.id);
    } else {
      await api.addBookmark(jobId);
    }
    refreshBookmarks();
  }

  async function trackApplication(jobId: string) {
    await api.addApplication(jobId, "saved");
    refreshApplications();
    setTab("applications");
  }

  async function updateApplicationStatus(id: string, status: ApplicationStatus) {
    await api.updateApplication(id, { status });
    refreshApplications();
  }

  async function removeApplication(id: string) {
    await api.removeApplication(id);
    refreshApplications();
  }

  const bookmarkedJobs = bookmarks.map((b) => b.job).filter((j): j is Job => !!j);

  return (
    <main className="max-w-6xl mx-auto px-4 py-6 flex flex-col gap-6">
      <header className="flex justify-between items-center flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">DataScience Career Tracker AI</h1>
          <p className="text-sm text-ink-secondary dark:text-ink-secondary-dark">
            Fresher &amp; 0–2 yr Data Science roles across {stats?.companies_tracked ?? 50} companies · scanned every 15 min
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <ExportButtons />
          <DarkModeToggle />
        </div>
      </header>

      <StatsCards stats={stats} />

      <nav className="flex gap-1 border-b border-line-hairline dark:border-line-hairline-dark">
        {(
          [
            ["jobs", `Jobs (${total})`],
            ["bookmarks", `Bookmarks (${bookmarks.length})`],
            ["applications", `Application tracker (${applications.length})`],
          ] as [Tab, string][]
        ).map(([value, label]) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === value
                ? "border-series-1 text-series-1"
                : "border-transparent text-ink-secondary dark:text-ink-secondary-dark hover:text-ink-primary dark:hover:text-ink-primary-dark"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "jobs" && (
        <div className="flex flex-col gap-4">
          <FiltersBar filters={filters} onChange={setFilters} companies={companies} />
          <JobList
            jobs={jobs}
            loading={jobsLoading}
            bookmarkedJobIds={bookmarkedJobIds}
            onToggleBookmark={toggleBookmark}
            onTrackApplication={trackApplication}
          />
        </div>
      )}

      {tab === "bookmarks" && (
        <JobList
          jobs={bookmarkedJobs}
          loading={false}
          bookmarkedJobIds={bookmarkedJobIds}
          onToggleBookmark={toggleBookmark}
          onTrackApplication={trackApplication}
        />
      )}

      {tab === "applications" && (
        <ApplicationTracker
          applications={applications}
          onUpdateStatus={updateApplicationStatus}
          onRemove={removeApplication}
        />
      )}
    </main>
  );
}
