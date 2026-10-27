import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCases } from "@/api/cases";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { SearchInput } from "@/components/shared/SearchInput";
import { StatusBadge, PriorityBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Case, CaseStatus, Priority, CaseFilterParams } from "@/types";
import { ExternalLink, AlertTriangle, Download, Filter, X } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// ── Columns ───────────────────────────────────────────────────────────────────

const columns: ColumnDef<Case>[] = [
  {
    key: "case_number",
    header: "Case ID",
    cell: (row) => {
      const isOverdue = !!row.expected_disposal_date && new Date(row.expected_disposal_date) < new Date() && row.status !== "disposed" && row.status !== "closed";
      return (
        <div>
          <span className="font-mono text-sm font-medium text-indigo-700">{row.case_number}</span>
          {isOverdue && (
            <div className="flex items-center gap-1 text-red-500 text-xs mt-0.5">
              <AlertTriangle className="h-3 w-3" /> Overdue
            </div>
          )}
        </div>
      );
    },
  },
  {
    key: "institution_id",
    header: "Institution / Bureau",
    cell: (row) => (
      <div>
        <p className="text-xs text-gray-400">{row.bureau?.code ?? "—"}</p>
      </div>
    ),
  },
  {
    key: "subject",
    header: "Subject",
    cell: (row) => <span className="text-sm text-gray-700 line-clamp-1">{row.subject}</span>,
  },
  {
    key: "category",
    header: "Category",
    cell: (row) => <span className="text-xs text-gray-600">{row.category?.name ?? "—"}</span>,
  },
  {
    key: "status",
    header: "Status",
    cell: (row) => <StatusBadge status={row.status} />,
  },
  {
    key: "priority",
    header: "Priority",
    cell: (row) => <PriorityBadge priority={row.priority} />,
  },
  {
    key: "assigned_officer",
    header: "Assigned To",
    cell: (row) =>
      row.assigned_officer ? (
        <span className="text-sm text-gray-700">{row.assigned_officer.full_name}</span>
      ) : (
        <Badge variant="secondary">Unassigned</Badge>
      ),
  },
  {
    key: "expected_disposal_date",
    header: "SLA Deadline",
    sortable: true,
    cell: (row) => {
      const isOverdue = !!row.expected_disposal_date && new Date(row.expected_disposal_date) < new Date() && row.status !== "disposed" && row.status !== "closed";
      return (
        <span className={`text-sm ${isOverdue ? "text-red-600 font-medium" : "text-gray-600"}`}>
          {row.expected_disposal_date ? formatDate(row.expected_disposal_date) : "—"}
        </span>
      );
    },
  },
  {
    key: "actions",
    header: "",
    cell: (row) => (
      <a
        href={`/cases/${row.id}`}
        className="text-indigo-600 hover:underline text-sm flex items-center gap-1"
      >
        View <ExternalLink className="h-3 w-3" />
      </a>
    ),
  },
];

// ── Export helper ─────────────────────────────────────────────────────────────

async function exportCases(params: CaseFilterParams & Record<string, unknown>) {
  try {
    const response = await apiClient.get("/reports/cases", {
      params: { ...params, format: "csv" },
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "cases_export.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    toast({ title: "Export failed", description: (err as Error).message, variant: "destructive" });
  }
}

// ── Filter bar ────────────────────────────────────────────────────────────────

interface Filters {
  search: string;
  status: CaseStatus | "";
  priority: Priority | "";
  bureau_id: string;
  is_overdue: "" | "true";
  date_from: string;
  date_to: string;
}

const STATUSES: CaseStatus[] = [
  "open", "pending_assignment", "under_process", "awaiting_information",
  "transferred", "escalated", "disposed", "closed",
];

const PRIORITIES: Priority[] = ["low", "medium", "high", "critical"];

function FilterPanel({
  filters,
  onChange,
  onClear,
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  onClear: () => void;
}) {
  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="flex flex-wrap gap-3 items-end bg-white border rounded-lg px-4 py-3">
      <Filter className="h-4 w-4 text-gray-400 shrink-0 self-center" />

      <div className="flex flex-col gap-1 min-w-[200px]">
        <label className="text-xs text-gray-500 font-medium">Search</label>
        <SearchInput
          value={filters.search}
          onChange={(v) => onChange({ ...filters, search: v })}
          placeholder="Case ID, institution..."
          className="h-9"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Status</label>
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value as CaseStatus | "" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Priority</label>
        <select
          value={filters.priority}
          onChange={(e) => onChange({ ...filters, priority: e.target.value as Priority | "" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Overdue</label>
        <select
          value={filters.is_overdue}
          onChange={(e) => onChange({ ...filters, is_overdue: e.target.value as "" | "true" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All</option>
          <option value="true">Overdue only</option>
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">From</label>
        <input
          type="date"
          value={filters.date_from}
          onChange={(e) => onChange({ ...filters, date_from: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">To</label>
        <input
          type="date"
          value={filters.date_to}
          onChange={(e) => onChange({ ...filters, date_to: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={onClear} className="self-end">
          <X className="mr-1 h-3.5 w-3.5" />
          Clear
        </Button>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

const EMPTY_FILTERS: Filters = {
  search: "",
  status: "",
  priority: "",
  bureau_id: "",
  is_overdue: "",
  date_from: "",
  date_to: "",
};

export default function CaseListPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  const queryParams: CaseFilterParams = {
    search: filters.search || undefined,
    status: filters.status || undefined,
    priority: filters.priority || undefined,
    bureau_id: filters.bureau_id || undefined,
    is_overdue: filters.is_overdue === "true" ? true : undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    page,
    size: 20,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["cases", queryParams],
    queryFn: () => getCases(queryParams),
  });

  const handleFilterChange = (f: Filters) => {
    setFilters(f);
    setPage(1);
  };

  return (
    <div>
      <PageHeader
        title="Cases"
        subtitle="All active and historical cases across bureaus"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Cases" }]}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportCases(queryParams as CaseFilterParams & Record<string, unknown>)}
          >
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <FilterPanel
          filters={filters}
          onChange={handleFilterChange}
          onClear={() => { setFilters(EMPTY_FILTERS); setPage(1); }}
        />

        {data && (
          <p className="text-sm text-gray-500">
            {data.total} case{data.total !== 1 ? "s" : ""} found
          </p>
        )}

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No cases found matching the selected filters."
          pagination={
            data
              ? { page: data.page, size: data.page_size, total: data.total, pages: data.pages }
              : undefined
          }
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}
