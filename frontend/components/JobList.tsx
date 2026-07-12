"use client";

import type { Job } from "@/lib/types";
import { JobCard } from "./JobCard";

export function JobList({
  jobs,
  loading,
  bookmarkedJobIds,
  onToggleBookmark,
  onTrackApplication,
}: {
  jobs: Job[];
  loading: boolean;
  bookmarkedJobIds: Set<string>;
  onToggleBookmark: (jobId: string) => void;
  onTrackApplication: (jobId: string) => void;
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card p-4 h-48 animate-pulse" />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <p className="text-sm text-ink-secondary dark:text-ink-secondary-dark py-8 text-center">
        No matching jobs yet. The tracker scans every 15 minutes — check back soon, or adjust your filters.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          bookmarked={bookmarkedJobIds.has(job.id)}
          onToggleBookmark={() => onToggleBookmark(job.id)}
          onTrackApplication={() => onTrackApplication(job.id)}
        />
      ))}
    </div>
  );
}
