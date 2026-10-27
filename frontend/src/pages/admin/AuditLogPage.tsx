import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { SearchInput } from "@/components/shared/SearchInput";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AuditLog, PaginatedResponse } from "@/types";
import { formatDateTime } from "@/lib/utils";
import { Shield, ChevronDown, ChevronRight } from "lucide-react";

function JsonViewer({ data, label }: { data: Record<string, unknown> | null; label: string }) {
  const [expanded, setExpanded] = useState(false);
  if (!data || Object.keys(data).length === 0) return <span className="text-gray-400 text-xs">—</span>;
  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-indigo-600 hover:underline"
      >
        {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        {label}
      </button>
      {expanded && (
        <pre className="mt-1 text-xs bg-gray-50 border rounded p-2 max-w-xs overflow-auto max-h-32">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

const ENTITY_TYPES = [
  "", "institution", "complaint", "case", "overlap_alert", "user", "document", "sla_rule",
];

const ACTIONS = [
  "", "create", "update", "delete", "assign", "transfer", "status_change", "login", "logout",
];

export default function AuditLogPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [entityType, setEntityType] = useState("");
  const [action, setAction] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", { search, page, entityType, action, dateFrom, dateTo }],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, size: 25 };
      if (search) params.search = search;
      if (entityType) params.entity_type = entityType;
      if (action) params.action = action;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const response = await apiClient.get<PaginatedResponse<AuditLog>>("/audit-logs", { params });
      return response.data;
    },
  });

  const columns: ColumnDef<AuditLog>[] = [
    {
      key: "timestamp",
      header: "Timestamp",
      sortable: true,
      cell: (row) => (
        <span className="text-xs font-mono text-gray-700">{formatDateTime(row.timestamp)}</span>
      ),
    },
    {
      key: "actor",
      header: "Actor",
      cell: (row) => (
        <div>
          <p className="text-sm font-medium text-gray-900">{row.actor_email}</p>
          <p className="text-xs text-gray-400">{row.actor_email}</p>
        </div>
      ),
    },
    {
      key: "entity_type",
      header: "Entity",
      cell: (row) => (
        <div>
          <Badge variant="secondary" className="text-xs capitalize mb-0.5">
            {row.entity_type.replace(/_/g, " ")}
          </Badge>
          <p className="text-xs text-gray-400 font-mono truncate max-w-[120px]">{row.entity_id}</p>
        </div>
      ),
    },
    {
      key: "action",
      header: "Action",
      cell: (row) => (
        <Badge
          variant={
            row.action === "delete" ? "destructive" :
            row.action === "create" ? "success" :
            "outline"
          }
          className="capitalize text-xs"
        >
          {row.action.replace(/_/g, " ")}
        </Badge>
      ),
    },
    {
      key: "before_state",
      header: "Before",
      cell: (row) => <JsonViewer data={row.old_value} label="Show before" />,
    },
    {
      key: "after_state",
      header: "After",
      cell: (row) => <JsonViewer data={row.new_value} label="Show after" />,
    },
    {
      key: "remarks",
      header: "Remarks",
      cell: (row) => (
        <span className="text-sm text-gray-600 line-clamp-1">{row.remarks ?? "—"}</span>
      ),
    },
    {
      key: "actions",
      header: "",
      cell: (row) => (
        <Button
          variant="ghost"
          size="sm"
          className="text-xs"
          onClick={() => setSelectedLog(row)}
        >
          Details
        </Button>
      ),
    },
  ];

  const resetFilters = () => {
    setSearch("");
    setEntityType("");
    setAction("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  return (
    <div>
      <PageHeader
        title="Audit Log"
        subtitle="Read-only history of all system actions and changes"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Administration" },
          { label: "Audit Log" },
        ]}
      />

      <div className="p-6 space-y-4">
        <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 flex items-center gap-2">
          <Shield className="h-4 w-4 text-blue-600 shrink-0" />
          <p className="text-sm text-blue-800">
            Audit records are read-only. No modifications are permitted to preserve the integrity of the audit trail.
          </p>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap gap-3 items-end">
          <SearchInput
            value={search}
            onChange={(val) => { setSearch(val); setPage(1); }}
            placeholder="Search by actor, entity ID..."
            className="w-64"
          />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 font-medium">Entity Type</label>
            <select
              value={entityType}
              onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>{t ? t.replace(/_/g, " ") : "All entities"}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 font-medium">Action</label>
            <select
              value={action}
              onChange={(e) => { setAction(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {ACTIONS.map((a) => (
                <option key={a} value={a}>{a ? a.replace(/_/g, " ") : "All actions"}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 font-medium">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 font-medium">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
              className="h-9 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          {(search || entityType || action || dateFrom || dateTo) && (
            <Button variant="ghost" size="sm" onClick={resetFilters} className="self-end">
              Clear filters
            </Button>
          )}
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No audit records found for the selected filters."
          pagination={
            data
              ? { page: data.page, size: data.page_size, total: data.total, pages: data.pages }
              : undefined
          }
          onPageChange={setPage}
        />
      </div>

      {/* Detail modal */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit Log Detail</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-4 text-sm pr-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">Timestamp</p>
                    <p className="font-mono text-gray-900">{formatDateTime(selectedLog.timestamp)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">Actor</p>
                    <p className="text-gray-900">{selectedLog.actor_email}</p>
                    <p className="text-xs text-gray-500">{selectedLog.actor_email}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">Entity Type</p>
                    <p className="text-gray-900 capitalize">{selectedLog.entity_type.replace(/_/g, " ")}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">Entity ID</p>
                    <p className="font-mono text-xs text-gray-900 break-all">{selectedLog.entity_id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">Action</p>
                    <Badge className="capitalize">{selectedLog.action.replace(/_/g, " ")}</Badge>
                  </div>
                  {selectedLog.ip_address && (
                    <div>
                      <p className="text-xs text-gray-400 uppercase font-medium">IP Address</p>
                      <p className="font-mono text-gray-900">{selectedLog.ip_address}</p>
                    </div>
                  )}
                </div>
                {selectedLog.remarks && (
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium mb-1">Remarks</p>
                    <p className="text-gray-700">{selectedLog.remarks}</p>
                  </div>
                )}
                {selectedLog.old_value && (
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium mb-1">Before State</p>
                    <pre className="text-xs bg-gray-50 border rounded p-3 overflow-auto max-h-48">
                      {JSON.stringify(selectedLog.old_value, null, 2)}
                    </pre>
                  </div>
                )}
                {selectedLog.new_value && (
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium mb-1">After State</p>
                    <pre className="text-xs bg-gray-50 border rounded p-3 overflow-auto max-h-48">
                      {JSON.stringify(selectedLog.new_value, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
