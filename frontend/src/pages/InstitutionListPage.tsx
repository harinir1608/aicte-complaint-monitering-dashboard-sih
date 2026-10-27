import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getInstitutions } from "@/api/institutions";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { SearchInput } from "@/components/shared/SearchInput";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Institution } from "@/types";
import { Plus, ExternalLink, Filter, X } from "lucide-react";
import type { InstitutionFilters } from "@/api/institutions";

// ── Columns ───────────────────────────────────────────────────────────────────

const columns: ColumnDef<Institution>[] = [
  {
    key: "name",
    header: "Institution Name",
    sortable: true,
    cell: (row) => (
      <div>
        <p className="font-medium text-gray-900">{row.name}</p>
        {row.permanent_id && (
          <p className="text-xs text-gray-400">ID: {row.permanent_id}</p>
        )}
      </div>
    ),
  },
  {
    key: "state",
    header: "State",
    cell: (row) => (
      <p className="text-sm text-gray-700">{row.state ?? "—"}</p>
    ),
  },
  {
    key: "institution_type",
    header: "Type",
    cell: (row) => <span className="text-sm capitalize">{row.institution_type?.replace(/_/g, " ") ?? "—"}</span>,
  },
  {
    key: "is_active",
    header: "Status",
    cell: (row) => (
      <Badge variant={row.is_active ? "default" : "secondary"}>
        {row.is_active ? "Active" : "Inactive"}
      </Badge>
    ),
  },
  {
    key: "actions",
    header: "",
    cell: (row) => (
      <a
        href={`/institutions/${row.id}`}
        className="text-indigo-600 hover:underline text-sm flex items-center gap-1"
      >
        View <ExternalLink className="h-3 w-3" />
      </a>
    ),
  },
];

// ── Filters ───────────────────────────────────────────────────────────────────

// Must match backend institution_type values (lowercase)
const INSTITUTION_TYPES = [
  { label: "Engineering", value: "engineering" },
  { label: "Management", value: "management" },
  { label: "Pharmacy", value: "pharmacy" },
  { label: "Polytechnic", value: "polytechnic" },
  { label: "Architecture", value: "architecture" },
  { label: "Other", value: "other" },
];

const STATES = [
  "Andhra Pradesh","Assam","Bihar","Chandigarh","Chhattisgarh","Delhi",
  "Goa","Gujarat","Haryana","Himachal Pradesh","Jammu & Kashmir",
  "Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra",
  "Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Puducherry",
  "Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
  "Uttar Pradesh","Uttarakhand","West Bengal",
];

interface UIFilters {
  search: string;
  state: string;
  institution_type: string;
  is_active: string;
}

const EMPTY: UIFilters = { search: "", state: "", institution_type: "", is_active: "" };

function FilterPanel({
  filters,
  onChange,
  onClear,
}: {
  filters: UIFilters;
  onChange: (f: UIFilters) => void;
  onClear: () => void;
}) {
  const hasFilters = Object.values(filters).some(Boolean);
  return (
    <div className="flex flex-wrap gap-3 items-end bg-white border rounded-lg px-4 py-3">
      <Filter className="h-4 w-4 text-gray-400 shrink-0 self-center" />

      <div className="flex flex-col gap-1 min-w-[220px]">
        <label className="text-xs text-gray-500 font-medium">Search</label>
        <SearchInput
          value={filters.search}
          onChange={(v) => onChange({ ...filters, search: v })}
          placeholder="Name, AICTE Permanent ID..."
          className="h-9"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">State</label>
        <select
          value={filters.state}
          onChange={(e) => onChange({ ...filters, state: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All states</option>
          {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Type</label>
        <select
          value={filters.institution_type}
          onChange={(e) => onChange({ ...filters, institution_type: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All types</option>
          {INSTITUTION_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">Status</label>
        <select
          value={filters.is_active}
          onChange={(e) => onChange({ ...filters, is_active: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All</option>
          <option value="true">Active only</option>
          <option value="false">Inactive only</option>
        </select>
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

export default function InstitutionListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<UIFilters>(EMPTY);
  const [page, setPage] = useState(1);

  const queryParams: InstitutionFilters = {
    search: filters.search || undefined,       // mapped to `name` in api.ts
    state: filters.state || undefined,
    institution_type: filters.institution_type || undefined,
    is_active:
      filters.is_active === "true"
        ? true
        : filters.is_active === "false"
        ? false
        : undefined,
    page,
    size: 20,                                  // backend accepts `size` as alias
  };

  const { data, isLoading } = useQuery({
    queryKey: ["institutions", queryParams],
    queryFn: () => getInstitutions(queryParams),
  });

  return (
    <div>
      <PageHeader
        title="Institution Directory"
        subtitle="Search and manage all registered AICTE institutions"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Institutions" }]}
        actions={
          <Button onClick={() => navigate("/institutions/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Add Institution
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <FilterPanel
          filters={filters}
          onChange={(f) => { setFilters(f); setPage(1); }}
          onClear={() => { setFilters(EMPTY); setPage(1); }}
        />

        {data && (
          <p className="text-sm text-gray-500">
            {data.total} institution{data.total !== 1 ? "s" : ""} found
          </p>
        )}

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No institutions found matching the selected filters."
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
