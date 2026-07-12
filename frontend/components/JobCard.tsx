"use client";

import type { Job } from "@/lib/types";

function matchColor(score: number | null): string {
  if (score === null) return "#898781";
  if (score >= 75) return "#0ca30c";
  if (score >= 50) return "#eda100";
  return "#d03b3b";
}

export function JobCard({
  job,
  bookmarked,
  onToggleBookmark,
  onTrackApplication,
}: {
  job: Job;
  bookmarked: boolean;
  onToggleBookmark: () => void;
  onTrackApplication: () => void;
}) {
  const skills = (job.skills || job.ai_skills || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="card p-4 flex flex-col gap-2">
      <div className="flex justify-between items-start gap-2">
        <div>
          <h3 className="font-semibold text-lg leading-tight">{job.title}</h3>
          <p className="text-sm text-ink-secondary dark:text-ink-secondary-dark">
            {job.company?.name || "Unknown company"} · {job.location}
          </p>
        </div>
        <button
          onClick={onToggleBookmark}
          aria-label="Bookmark job"
          className="text-xl leading-none px-1"
          title={bookmarked ? "Remove bookmark" : "Bookmark"}
        >
          {bookmarked ? "★" : "☆"}
        </button>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-secondary dark:text-ink-secondary-dark">
        <span>Experience: {job.experience_required || "Not specified"}</span>
        <span>Salary: {job.salary || "Not disclosed"}</span>
        {job.posted_date && <span>Posted: {new Date(job.posted_date).toLocaleDateString()}</span>}
        {job.is_internship && <span className="text-status-warning font-medium">Internship</span>}
      </div>

      {job.ai_summary && <p className="text-sm">{job.ai_summary}</p>}

      {skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((s) => (
            <span
              key={s}
              className="text-xs rounded-full px-2 py-0.5 bg-plane dark:bg-plane-dark border border-line-hairline dark:border-line-hairline-dark"
            >
              {s}
            </span>
          ))}
        </div>
      )}

      {job.resume_match_score !== null && (
        <div className="text-sm flex items-center gap-2">
          <span className="font-medium" style={{ color: matchColor(job.resume_match_score) }}>
            {job.resume_match_score}/100 resume match
          </span>
          {job.resume_match_notes && (
            <span className="text-ink-secondary dark:text-ink-secondary-dark">{job.resume_match_notes}</span>
          )}
        </div>
      )}

      {job.learning_recommendations && (
        <p className="text-xs text-ink-muted italic">💡 {job.learning_recommendations}</p>
      )}

      <div className="flex gap-2 mt-1">
        <a
          href={job.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium rounded-md px-3 py-1.5 bg-series-1 text-white hover:opacity-90 transition-opacity"
        >
          Apply
        </a>
        <button
          onClick={onTrackApplication}
          className="text-sm font-medium rounded-md px-3 py-1.5 border border-line-hairline dark:border-line-hairline-dark hover:bg-plane dark:hover:bg-plane-dark transition-colors"
        >
          Track application
        </button>
      </div>
    </div>
  );
}
