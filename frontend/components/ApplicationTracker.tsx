"use client";

import type { Application, ApplicationStatus } from "@/lib/types";

const STATUS_OPTIONS: { value: ApplicationStatus; label: string; color: string }[] = [
  { value: "saved", label: "Saved", color: "#898781" },
  { value: "applied", label: "Applied", color: "#2a78d6" },
  { value: "in_progress", label: "In progress", color: "#eda100" },
  { value: "interviewing", label: "Interviewing", color: "#4a3aa7" },
  { value: "offer", label: "Offer", color: "#0ca30c" },
  { value: "rejected", label: "Rejected", color: "#d03b3b" },
  { value: "withdrawn", label: "Withdrawn", color: "#52514e" },
];

export function ApplicationTracker({
  applications,
  onUpdateStatus,
  onRemove,
}: {
  applications: Application[];
  onUpdateStatus: (id: string, status: ApplicationStatus) => void;
  onRemove: (id: string) => void;
}) {
  if (applications.length === 0) {
    return (
      <p className="text-sm text-ink-secondary dark:text-ink-secondary-dark">
        No applications tracked yet. Click &quot;Track application&quot; on a job to add it here.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto card">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-ink-secondary dark:text-ink-secondary-dark border-b border-line-hairline dark:border-line-hairline-dark">
            <th className="p-3">Role</th>
            <th className="p-3">Company</th>
            <th className="p-3">Status</th>
            <th className="p-3">Updated</th>
            <th className="p-3"></th>
          </tr>
        </thead>
        <tbody>
          {applications.map((app) => {
            const statusMeta = STATUS_OPTIONS.find((s) => s.value === app.status);
            return (
              <tr key={app.id} className="border-b border-line-hairline dark:border-line-hairline-dark last:border-0">
                <td className="p-3 font-medium">{app.job?.title || "—"}</td>
                <td className="p-3">{app.job?.company?.name || "—"}</td>
                <td className="p-3">
                  <select
                    value={app.status}
                    onChange={(e) => onUpdateStatus(app.id, e.target.value as ApplicationStatus)}
                    className="rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-2 py-1"
                    style={{ color: statusMeta?.color }}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="p-3 tabular text-ink-secondary dark:text-ink-secondary-dark">
                  {new Date(app.updated_at).toLocaleDateString()}
                </td>
                <td className="p-3">
                  <button
                    onClick={() => onRemove(app.id)}
                    className="text-ink-muted hover:text-status-critical transition-colors"
                    aria-label="Remove application"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
