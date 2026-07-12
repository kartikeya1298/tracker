import type { Stats } from "@/lib/types";

function StatTile({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wide text-ink-secondary dark:text-ink-secondary-dark">
        {label}
      </span>
      <span className="text-3xl font-semibold tabular" style={accent ? { color: accent } : undefined}>
        {value}
      </span>
    </div>
  );
}

export function StatsCards({ stats }: { stats: Stats | null }) {
  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card p-4 h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatTile label="Total jobs found" value={stats.total_jobs} accent="#2a78d6" />
      <StatTile label="Jobs posted today" value={stats.jobs_today} accent="#1baf7a" />
      <StatTile label="This week" value={stats.jobs_this_week} />
      <StatTile label="Companies tracked" value={stats.companies_tracked} />
    </div>
  );
}
