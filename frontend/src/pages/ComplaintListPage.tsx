import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getComplaints } from "@/api/complaints";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { SearchInput } from "@/components/shared/SearchInput";
import { StatusBadge, PriorityBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";

import type { Complaint, ComplaintStatus, Priority, ComplaintFilterParams } from "@/types";
import { Plus, ExternalLink, Filter, X } from "lucide-react";
import { formatDate } from "@/lib/utils";

// ── Columns ───────────────────────────────────────────────────────────────────

const columns: ColumnDef<Complaint>[] = [
  {
    key: "complaint_number",
    header: "Complaint ID",
    cell: (row) => (
      <span className="font-mono text-sm font-medium text-indigo-700">
        {row.complaint_number}
      </span>
    ),
  },
  {
    key: "institution",
    header: "Institution",
    cell: (row) => (
      <div>
        <p className="text-sm font-medium text-gray-900 line-clamp-1">
          {row.institution?.name ?? row.institution_name_raw ?? "—"}
        </p>
        <p className="text-xs text-gray-400">{row.bureau?.code ?? "—"}</p>
      </div>
    ),
  },
  {
    key: "category",
    header: "Category",
    cell: (row) => <span className="text-xs text-gray-700">{row.category?.name ?? "—"}</span>,
  },
  {
    key: "subject",
    header: "Subject",
    cell: (row) => (
      <span className="text-sm text-gray-700 line-clamp-1">{row.subject}</span>
    ),
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
    key: "source",
    header: "Source",
    cell: (row) => <span className="text-xs text-gray-600 capitalize">{(row.source as string).replace(/_/g, " ")}</span>,
  },
  {
    key: "received_date",
    header: "Received",
    sortable: true,
    cell: (row) => (
      <span className="text-sm text-gray-600">{formatDate(row.received_date)}</span>
    ),
  },
  {
    key: "actions",
    header: "",
    cell: (row) => (
      <a
        href={`/complaints/${row.id}`}
        className="text-indigo-600 hover:underline text-sm flex items-center gap-1"
      >
        View <ExternalLink className="h-3 w-3" />
      </a>
    ),
  },
];

// ── Filters ───────────────────────────────────────────────────────────────────

interface Filters {
  search: string;
  status: ComplaintStatus | "";
  priority: Priority | "";
  category: string;
  bureau_id: string;
  date_from: string;
  date_to: string;
}

const COMPLAINT_STATUSES: ComplaintStatus[] = [
  "received", "pending_assignment", "under_process", "awaiting_information",
  "transferred", "escalated", "disposed", "closed",
];

const PRIORITIES: Priority[] = ["low", "medium", "high", "critical"];

const EMPTY_FILTERS: Filters = {
  search: "",
  status: "",
  priority: "",
  category: "",
  bureau_id: "",
  date_from: "",
  date_to: "",
};

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
          placeholder="Complaint number, institution, subject..."
          className="h-9"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Status</label>
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value as ComplaintStatus | "" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All statuses</option>
          {COMPLAINT_STATUSES.map((s) => (
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
        <label className="text-xs text-gray-500 font-medium">Category</label>
        <input
          type="text"
          value={filters.category}
          onChange={(e) => onChange({ ...filters, category: e.target.value })}
          placeholder="e.g. Fee Refund"
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm w-36 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
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

export default function ComplaintListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  const queryParams: ComplaintFilterParams = {
    search: filters.search || undefined,
    status: filters.status || undefined,
    priority: filters.priority || undefined,
    category: filters.category || undefined,
    bureau_id: filters.bureau_id || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    page,
    size: 20,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["complaints", queryParams],
    queryFn: () => getComplaints(queryParams),
  });

  return (
    <div>
      <PageHeader
        title="Complaints"
        subtitle="All registered complaints across bureaus"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Complaints" }]}
        actions={
          <Button onClick={() => navigate("/complaints/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Register Complaint
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <FilterPanel
          filters={filters}
          onChange={(f) => { setFilters(f); setPage(1); }}
          onClear={() => { setFilters(EMPTY_FILTERS); setPage(1); }}
        />

        {data && (
          <p className="text-sm text-gray-500">
            {data.total} complaint{data.total !== 1 ? "s" : ""} found
          </p>
        )}

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No complaints found matching the selected filters."
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
