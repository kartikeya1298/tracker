import { api } from "@/lib/api";

export function ExportButtons() {
  return (
    <div className="flex gap-2">
      <a
        href={api.exportUrl("csv")}
        className="text-sm font-medium rounded-md px-3 py-2 card hover:bg-plane dark:hover:bg-plane-dark transition-colors"
      >
        Export CSV
      </a>
      <a
        href={api.exportUrl("xlsx")}
        className="text-sm font-medium rounded-md px-3 py-2 card hover:bg-plane dark:hover:bg-plane-dark transition-colors"
      >
        Export Excel
      </a>
    </div>
  );
}
