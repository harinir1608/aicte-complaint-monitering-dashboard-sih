import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getConflicts } from "@/api/conflicts";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, Building2, ExternalLink } from "lucide-react";
import type { ConflictSeverity, ConflictStatus } from "@/types";
import { formatDate } from "@/lib/utils";

const SEVERITY_COLORS: Record<ConflictSeverity, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-blue-100 text-blue-800",
};

const STATUS_COLORS: Record<ConflictStatus, string> = {
  open: "bg-red-50 text-red-700",
  acknowledged: "bg-amber-50 text-amber-700",
  resolved: "bg-green-50 text-green-700",
  dismissed: "bg-gray-100 text-gray-500",
};

const RULE_LABELS: Record<string, string> = {
  multi_bureau_same_issue: "Multi-Bureau Active Cases",
  overlapping_officer_actions: "Overlapping Officer Actions",
  competing_deadlines: "Competing Deadlines",
  transfer_while_related_active: "Transfer with Active Related Case",
};

export default function ConflictListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<{
    severity?: string;
    status?: string;
    page: number;
  }>({ page: 1 });

  const { data, isLoading } = useQuery({
    queryKey: ["conflicts", filters],
    queryFn: () =>
      getConflicts({
        severity: filters.severity,
        status: filters.status,
        page: filters.page,
        page_size: 20,
      }),
  });

  return (
    <div>
      <PageHeader
        title="Cross-Bureau Conflict Warnings"
        subtitle="Rule-based detection of potentially conflicting actions across bureaus"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Conflicts" },
        ]}
      />

      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center bg-white border rounded-lg px-4 py-3">
          <select
            value={filters.severity ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value || undefined, page: 1 }))}
            className="h-8 rounded border border-gray-300 px-2 text-xs"
          >
            <option value="">All Severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={filters.status ?? ""}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value || undefined, page: 1 }))}
            className="h-8 rounded border border-gray-300 px-2 text-xs"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
          {(filters.severity || filters.status) && (
            <Button variant="ghost" size="sm" className="text-xs" onClick={() => setFilters({ page: 1 })}>
              Clear
            </Button>
          )}
        </div>

        {/* List */}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}
          </div>
        ) : !data?.items.length ? (
          <Card>
            <CardContent className="py-12 text-center text-sm text-gray-400">
              No conflict warnings found. Run a conflict scan to detect coordination issues.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {data.items.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start justify-between rounded-lg border border-gray-200 bg-white p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/conflicts/${alert.id}`)}
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className={`h-5 w-5 mt-0.5 shrink-0 ${alert.severity === "high" ? "text-red-500" : alert.severity === "medium" ? "text-amber-500" : "text-blue-500"}`} />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900">
                        {RULE_LABELS[alert.rule_triggered] ?? alert.rule_triggered.replace(/_/g, " ")}
                      </span>
                      <Badge className={`text-xs ${SEVERITY_COLORS[alert.severity]}`}>{alert.severity}</Badge>
                      <Badge className={`text-xs ${STATUS_COLORS[alert.status]}`}>{alert.status}</Badge>
                    </div>
                    {alert.institution_name && (
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Building2 className="h-3 w-3" />
                        {alert.institution_name}
                      </div>
                    )}
                    {alert.rule_description && (
                      <p className="text-xs text-gray-500 line-clamp-2">{alert.rule_description}</p>
                    )}
                    <p className="text-xs text-gray-400">
                      {(alert.case_ids ?? []).length} case(s) ·{" "}
                      {(alert.bureau_ids ?? []).length} bureau(s) · {formatDate(alert.created_at)}
                    </p>
                  </div>
                </div>
                <ExternalLink className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-gray-400">{data.total} total conflict alerts</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={filters.page <= 1} onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>Prev</Button>
              <span className="text-xs text-gray-500 self-center">{filters.page} / {data.pages}</span>
              <Button variant="outline" size="sm" disabled={filters.page >= data.pages} onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>Next</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
