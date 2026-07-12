"use client";

import type { Company } from "@/lib/types";
import type { JobFilters } from "@/lib/api";

const TARGET_ROLES = [
  "Data Analyst", "Business Analyst", "Junior Data Analyst", "Data Scientist",
  "Junior Data Scientist", "Associate Data Scientist", "Machine Learning Engineer",
  "Junior Machine Learning Engineer", "AI Engineer", "Applied Scientist",
  "Research Scientist (AI/ML)", "Data Engineer", "Analytics Engineer",
  "Business Intelligence Engineer", "BI Analyst", "Decision Scientist",
  "AI/ML Engineer", "Generative AI Engineer", "Statistical Analyst",
  "Quantitative Analyst (Entry Level)",
];

interface Props {
  filters: JobFilters;
  onChange: (filters: JobFilters) => void;
  companies: Company[];
}

export function FiltersBar({ filters, onChange, companies }: Props) {
  return (
    <div className="card p-4 flex flex-col gap-3">
      <input
        type="text"
        placeholder="Search title, skills, company..."
        value={filters.search || ""}
        onChange={(e) => onChange({ ...filters, search: e.target.value, offset: 0 })}
        className="w-full rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-series-1"
      />

      <div className="flex flex-wrap gap-3 items-center text-sm">
        <select
          multiple
          value={filters.role || []}
          onChange={(e) =>
            onChange({ ...filters, role: Array.from(e.target.selectedOptions, (o) => o.value), offset: 0 })
          }
          className="rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-2 py-1.5 min-w-[180px] h-24"
        >
          {TARGET_ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <select
          multiple
          value={filters.company || []}
          onChange={(e) =>
            onChange({ ...filters, company: Array.from(e.target.selectedOptions, (o) => o.value), offset: 0 })
          }
          className="rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-2 py-1.5 min-w-[180px] h-24"
        >
          {companies.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Location contains..."
          value={filters.location || ""}
          onChange={(e) => onChange({ ...filters, location: e.target.value, offset: 0 })}
          className="rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-2 py-1.5"
        />

        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={!!filters.india_only}
            onChange={(e) => onChange({ ...filters, india_only: e.target.checked, offset: 0 })}
          />
          India only
        </label>
        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={filters.include_remote !== false}
            onChange={(e) => onChange({ ...filters, include_remote: e.target.checked, offset: 0 })}
          />
          Include remote
        </label>
        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={!!filters.include_internships}
            onChange={(e) => onChange({ ...filters, include_internships: e.target.checked, offset: 0 })}
          />
          Include internships
        </label>

        <select
          value={filters.sort_by || "rank_score"}
          onChange={(e) => onChange({ ...filters, sort_by: e.target.value as JobFilters["sort_by"], offset: 0 })}
          className="rounded-md border border-line-hairline dark:border-line-hairline-dark bg-transparent px-2 py-1.5 ml-auto"
        >
          <option value="rank_score">Best match</option>
          <option value="posted_date">Newest posted</option>
          <option value="first_seen_at">Recently found</option>
          <option value="title">Title A-Z</option>
        </select>
      </div>
    </div>
  );
}
