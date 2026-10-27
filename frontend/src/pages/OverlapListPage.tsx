import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getOverlaps } from "@/api/overlaps";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { OverlapStatusBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { OverlapAlert, OverlapStatus, MatchType, OverlapFilterParams } from "@/types";
import { ExternalLink, AlertTriangle, Filter, X } from "lucide-react";
import { formatDate } from "@/lib/utils";

// ── Columns ───────────────────────────────────────────────────────────────────

const columns: ColumnDef<OverlapAlert>[] = [
  {
    key: "alert_number",
    header: "Alert ID",
    cell: (row) => (
      <span className="font-mono text-sm font-medium text-amber-700">{row.alert_number}</span>
    ),
  },
  {
    key: "institution_id",
    header: "Institution",
    cell: (row) => (
      <span className="text-sm font-medium text-gray-900 font-mono text-xs">
        {row.institution_id ? row.institution_id.slice(0, 8) + "…" : "—"}
      </span>
    ),
  },
  {
    key: "match_type",
    header: "Match Type",
    cell: (row) => (
      <Badge variant="secondary" className="text-xs capitalize">
        {(row.match_type as string).replace(/_/g, " ")}
      </Badge>
    ),
  },
  {
    key: "bureaus_involved",
    header: "Bureaus",
    cell: (row) => (
      <span className="text-xs text-gray-500">
        {Array.isArray(row.bureaus_involved) ? row.bureaus_involved.length + " bureau(s)" : "—"}
      </span>
    ),
  },
  {
    key: "match_score",
    header: "Match Score",
    cell: (row) =>
      row.match_score != null ? (
        <span className="text-sm font-medium">
          {Number(row.match_score).toFixed(0)}%
        </span>
      ) : (
        "—"
      ),
  },
  {
    key: "status",
    header: "Status",
    cell: (row) => <OverlapStatusBadge status={row.status} />,
  },
  {
    key: "created_at",
    header: "Created",
    sortable: true,
    cell: (row) => (
      <span className="text-sm text-gray-600">{formatDate(row.created_at)}</span>
    ),
  },
  {
    key: "actions",
    header: "",
    cell: (row) => (
      <a
        href={`/overlaps/${row.id}`}
        className="text-amber-600 hover:underline text-sm flex items-center gap-1"
      >
        Review <ExternalLink className="h-3 w-3" />
      </a>
    ),
  },
];

// ── Filters ───────────────────────────────────────────────────────────────────

const OVERLAP_STATUSES: OverlapStatus[] = [
  "pending_review", "confirmed_related", "false_positive", "separate_handling",
];

const MATCH_TYPES: MatchType[] = [
  "exact_id", "same_institution", "possible_institution", "related_complaint", "same_complaint_reference",
];

interface Filters {
  status: OverlapStatus | "";
  match_type: MatchType | "";
  date_from: string;
  date_to: string;
}

const EMPTY_FILTERS: Filters = { status: "", match_type: "", date_from: "", date_to: "" };

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

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Review Status</label>
        <select
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value as OverlapStatus | "" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All statuses</option>
          {OVERLAP_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Match Type</label>
        <select
          value={filters.match_type}
          onChange={(e) => onChange({ ...filters, match_type: e.target.value as MatchType | "" })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All match types</option>
          {MATCH_TYPES.map((m) => (
            <option key={m} value={m}>
              {m.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
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

// ── Stats bar ─────────────────────────────────────────────────────────────────

function StatsBar({ items }: { items: OverlapAlert[] }) {
  const counts: Record<string, number> = {};
  items.forEach((a) => {
    counts[a.status] = (counts[a.status] ?? 0) + 1;
  });
  const STATUS_LABEL: Record<string, string> = {
    pending_review: "Pending Review",
    confirmed_related: "Confirmed Related",
    false_positive: "False Positive",
    separate_handling: "Separate Handling",
  };
  const STATUS_COLOR: Record<string, string> = {
    pending_review: "bg-amber-100 text-amber-800",
    confirmed_related: "bg-blue-100 text-blue-800",
    false_positive: "bg-gray-100 text-gray-600",
    separate_handling: "bg-green-100 text-green-700",
  };
  return (
    <div className="flex flex-wrap gap-3">
      {Object.entries(STATUS_LABEL).map(([key, label]) => (
        <div
          key={key}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${STATUS_COLOR[key]}`}
        >
          {counts[key] ?? 0} {label}
        </div>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function OverlapListPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  const queryParams: OverlapFilterParams = {
    status: filters.status || undefined,
    match_type: filters.match_type || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    page,
    size: 20,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["overlaps", queryParams],
    queryFn: () => getOverlaps(queryParams),
  });

  const pendingCount = data?.items.filter((o) => o.status === "pending_review").length ?? 0;

  return (
    <div>
      <PageHeader
        title="Overlap Alerts"
        subtitle="Potential Overlapping Cases — Coordination Required"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Overlap Review" }]}
      />

      <div className="p-6 space-y-4">
        {pendingCount > 0 && (
          <div className="flex items-center gap-3 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
            <p className="text-sm text-amber-800 font-medium">
              {pendingCount} overlap alert{pendingCount !== 1 ? "s" : ""} pending review
            </p>
          </div>
        )}

        <FilterPanel
          filters={filters}
          onChange={(f) => { setFilters(f); setPage(1); }}
          onClear={() => { setFilters(EMPTY_FILTERS); setPage(1); }}
        />

        {data && data.items.length > 0 && <StatsBar items={data.items} />}

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No overlap alerts found."
          pagination={
            data
              ? { page: data.page, size: data.page_size ?? 20, total: data.total, pages: data.pages }
              : undefined
          }
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}
