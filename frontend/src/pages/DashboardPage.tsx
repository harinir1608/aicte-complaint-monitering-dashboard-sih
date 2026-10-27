import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getDashboardSummary,
  getDashboardTrends,
  getDashboardWorkload,
  getInstitutionTable,
  type DashboardFilters,
} from "@/api/dashboard";
import { PageHeader } from "@/components/shared/PageHeader";
import { KPICard } from "@/components/dashboard/KPICard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer,
} from "recharts";
import {
  FileText,
  Briefcase,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  GitMerge,
  Info,
  Building2,
  ExternalLink,
  Filter,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

// ── Colour palettes ───────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  received: "#6366f1",
  pending_assignment: "#f59e0b",
  under_process: "#3b82f6",
  awaiting_information: "#8b5cf6",
  transferred: "#06b6d4",
  escalated: "#f97316",
  disposed: "#22c55e",
  closed: "#94a3b8",
  open: "#6366f1",
};

const BUREAU_COLORS = ["#6366f1", "#3b82f6", "#06b6d4", "#8b5cf6", "#f59e0b", "#22c55e", "#f97316"];

// ── Ageing bucket data ─────────────────────────────────────────────────────────

const AGEING_BUCKETS = [
  { bucket: "0-7 days", count: 0 },
  { bucket: "8-15 days", count: 0 },
  { bucket: "16-30 days", count: 0 },
  { bucket: "31-60 days", count: 0 },
  { bucket: "60+ days", count: 0 },
];

// ── Filter bar ────────────────────────────────────────────────────────────────

function FilterBar({
  filters,
  onChange,
}: {
  filters: DashboardFilters;
  onChange: (f: DashboardFilters) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3 items-center bg-white border rounded-lg px-4 py-3">
      <Filter className="h-4 w-4 text-gray-400 shrink-0" />
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400">From</label>
        <input
          type="date"
          value={filters.date_from ?? ""}
          onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
          className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400">To</label>
        <input
          type="date"
          value={filters.date_to ?? ""}
          onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
          className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400">Category</label>
        <input
          type="text"
          value={filters.category ?? ""}
          onChange={(e) => onChange({ ...filters, category: e.target.value || undefined })}
          placeholder="All categories"
          className="h-8 rounded border border-gray-300 px-2 text-xs w-36 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400">Priority</label>
        <select
          value={filters.priority ?? ""}
          onChange={(e) => onChange({ ...filters, priority: e.target.value || undefined })}
          className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">All priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      {Object.values(filters).some(Boolean) && (
        <Button
          variant="ghost"
          size="sm"
          className="self-end text-xs"
          onClick={() => onChange({})}
        >
          Clear
        </Button>
      )}
    </div>
  );
}

// ── Institution row ────────────────────────────────────────────────────────────

interface InstitutionTableEntry {
  institution_id: string;
  institution_name: string;
  permanent_id: string | null;
  total_complaints: number;
  total_cases: number;
  active_cases: number;
  overdue_cases: number;
  overlap_count: number;
  latest_activity: string | null;
}

function InstitutionRow({ institution }: { institution: InstitutionTableEntry }) {
  const navigate = useNavigate();
  return (
    <tr
      className="border-b last:border-0 hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={() => navigate(`/institutions/${institution.institution_id}`)}
    >
      <td className="py-3 px-4">
        <div>
          <p className="text-sm font-medium text-gray-900">{institution.institution_name}</p>
          {institution.permanent_id && (
            <p className="text-xs text-gray-400">{institution.permanent_id}</p>
          )}
        </div>
      </td>
      <td className="py-3 px-4 text-center">
        <span className="font-semibold text-blue-700">{institution.total_complaints}</span>
      </td>
      <td className="py-3 px-4 text-center">
        <span className="font-semibold text-indigo-700">{institution.total_cases}</span>
      </td>
      <td className="py-3 px-4 text-center">
        <Badge variant={institution.active_cases > 0 ? "default" : "secondary"}>
          {institution.active_cases}
        </Badge>
      </td>
      <td className="py-3 px-4 text-center">
        {institution.overdue_cases > 0 ? (
          <span className="text-red-600 font-semibold">{institution.overdue_cases}</span>
        ) : (
          <span className="text-gray-400">0</span>
        )}
      </td>
      <td className="py-3 px-4 text-center">
        {institution.overlap_count > 0 ? (
          <span className="text-amber-600 font-semibold">{institution.overlap_count}</span>
        ) : (
          <span className="text-gray-400">0</span>
        )}
      </td>
      <td className="py-3 px-4 text-center">
        <span className="text-xs text-gray-500">{institution.latest_activity ? formatDate(institution.latest_activity) : "—"}</span>
      </td>
      <td className="py-3 px-4 text-center">
        <ExternalLink className="h-4 w-4 text-indigo-500 mx-auto" />
      </td>
    </tr>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [filters, setFilters] = useState<DashboardFilters>({});
  const [institutionSearch, setInstitutionSearch] = useState("");
  const [institutionPage, setInstitutionPage] = useState(1);

  const { data: summary, isLoading } = useQuery({
    queryKey: ["dashboard", "summary", filters],
    queryFn: () => getDashboardSummary(filters),
  });

  const { data: trends } = useQuery({
    queryKey: ["dashboard", "trends", filters],
    queryFn: () => getDashboardTrends(filters),
  });

  const { data: workload } = useQuery({
    queryKey: ["dashboard", "workload", filters],
    queryFn: () => getDashboardWorkload(filters),
  });

  const { data: institutionTable, isLoading: loadingInstitutions } = useQuery({
    queryKey: ["dashboard", "institutions", { ...filters, institutionSearch, institutionPage }],
    queryFn: () =>
      getInstitutionTable({ ...filters, search: institutionSearch, page: institutionPage, size: 10 }),
  });

  // Build status pie data from flat summary fields
  const statusPieData = summary ? [
    { name: "pending assignment", value: summary.pending_assignment, color: STATUS_COLORS.pending_assignment },
    { name: "under process", value: summary.under_process, color: STATUS_COLORS.under_process },
    { name: "awaiting info", value: summary.awaiting_information, color: STATUS_COLORS.awaiting_information },
    { name: "transferred", value: summary.transferred, color: STATUS_COLORS.transferred },
    { name: "escalated", value: summary.escalated, color: STATUS_COLORS.escalated },
    { name: "disposed", value: summary.disposed, color: STATUS_COLORS.disposed },
    { name: "closed", value: summary.closed, color: STATUS_COLORS.closed },
  ].filter(d => d.value > 0) : [];

  // Build bureau bar data from workload
  const bureauBarData = (workload ?? []).map(w => ({
    bureau_name: w.entity_name?.replace(" Bureau", "").replace(" Cell", "") ?? w.entity_name,
    count: w.total_cases,
    active: w.active_cases,
    overdue: w.overdue_cases,
  }));

  const ageing = AGEING_BUCKETS;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of complaints, cases, and overlap alerts across all bureaus"
        breadcrumbs={[{ label: "Home" }, { label: "Dashboard" }]}
      />

      <div className="p-6 space-y-6">
        {/* Filter bar */}
        <FilterBar filters={filters} onChange={(f) => { setFilters(f); setInstitutionPage(1); }} />

        {/* KPI Row 1 */}
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
          <KPICard
            title="Total Complaints"
            value={summary?.total_complaints ?? 0}
            icon={FileText}
            colorClass="text-blue-600 bg-blue-50"
            href="/complaints"
            isLoading={isLoading}
          />
          <KPICard
            title="Active Cases"
            value={summary?.active_cases ?? 0}
            icon={Briefcase}
            colorClass="text-indigo-600 bg-indigo-50"
            href="/cases"
            isLoading={isLoading}
          />
          <KPICard
            title="Overdue Cases"
            value={summary?.overdue_cases ?? 0}
            icon={AlertTriangle}
            colorClass="text-red-600 bg-red-50"
            href="/cases?is_overdue=true"
            isLoading={isLoading}
          />
          <KPICard
            title="Overlap Alerts"
            value={summary?.overlaps_pending_review ?? 0}
            icon={GitMerge}
            colorClass="text-amber-600 bg-amber-50"
            href="/overlaps?status=pending_review"
            isLoading={isLoading}
          />
          <KPICard
            title="Disposed"
            value={summary?.disposed ?? 0}
            icon={CheckCircle}
            colorClass="text-green-600 bg-green-50"
            isLoading={isLoading}
          />
        </div>

        {/* KPI Row 2 */}
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
          <KPICard
            title="Pending Assignment"
            value={summary?.pending_assignment ?? 0}
            icon={Clock}
            colorClass="text-yellow-600 bg-yellow-50"
            isLoading={isLoading}
          />
          <KPICard
            title="Under Process"
            value={summary?.under_process ?? 0}
            icon={Briefcase}
            colorClass="text-purple-600 bg-purple-50"
            isLoading={isLoading}
          />
          <KPICard
            title="Awaiting Info"
            value={summary?.awaiting_information ?? 0}
            icon={Info}
            colorClass="text-cyan-600 bg-cyan-50"
            isLoading={isLoading}
          />
          <KPICard
            title="Escalated"
            value={summary?.escalated ?? 0}
            icon={ArrowUpRight}
            colorClass="text-orange-600 bg-orange-50"
            isLoading={isLoading}
          />
          <KPICard
            title="Transferred"
            value={summary?.transferred ?? 0}
            icon={ArrowUpRight}
            colorClass="text-teal-600 bg-teal-50"
            isLoading={isLoading}
          />
          <KPICard
            title="Approaching Deadline"
            value={summary?.cases_approaching_deadline ?? 0}
            icon={Clock}
            colorClass="text-yellow-600 bg-yellow-50"
            href="/cases"
            isLoading={isLoading}
          />
          <KPICard
            title="Conflict Warnings"
            value={summary?.conflict_warnings_unresolved ?? 0}
            icon={AlertTriangle}
            colorClass="text-rose-600 bg-rose-50"
            href="/conflicts"
            isLoading={isLoading}
          />
        </div>

        {/* Charts row 1: Pie + Bar */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          {/* Cases by Status: Pie */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Cases by Status</CardTitle>
            </CardHeader>
            <CardContent>
              {statusPieData.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No data available</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={statusPieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                      labelLine={false}
                    >
                      {statusPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Cases by Bureau: Bar */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Cases by Bureau</CardTitle>
            </CardHeader>
            <CardContent>
              {bureauBarData.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No data available</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={bureauBarData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="bureau_name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Cases" radius={[4, 4, 0, 0]}>
                      {bureauBarData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={BUREAU_COLORS[index % BUREAU_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Charts row 2: Line + Ageing */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          {/* Monthly Intake & Disposal: Line */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Monthly Intake & Disposal (Last 12 Months)</CardTitle>
            </CardHeader>
            <CardContent>
              {!trends || trends.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No trend data available</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={trends} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="intake"
                      name="Intake"
                      stroke="#6366f1"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="disposed"
                      name="Disposed"
                      stroke="#22c55e"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="active"
                      name="Active"
                      stroke="#f97316"
                      strokeWidth={2}
                      strokeDasharray="4 2"
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Pending Case Ageing: Bar */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Pending Case Ageing</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={ageing} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Cases" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Regional Workload */}
        {workload && workload.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Regional Workload</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={workload} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="entity_name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total_cases" name="Total" fill="#6366f1" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="active_cases" name="Active" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="overdue_cases" name="Overdue" fill="#ef4444" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Institution Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Building2 className="h-4 w-4 text-gray-400" />
              Institution Summary
            </CardTitle>
            <input
              type="text"
              placeholder="Search institutions..."
              value={institutionSearch}
              onChange={(e) => { setInstitutionSearch(e.target.value); setInstitutionPage(1); }}
              className="h-8 rounded border border-gray-300 px-3 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </CardHeader>
          <CardContent className="p-0">
            {loadingInstitutions ? (
              <div className="p-6 space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Institution</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Complaints</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Cases</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Active</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Overdue</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Overlaps</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide text-center">Last Activity</th>
                        <th className="py-3 px-4 w-8"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {institutionTable?.items.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="py-8 text-center text-sm text-gray-400">
                            No institutions found.
                          </td>
                        </tr>
                      ) : (
                        institutionTable?.items.map((inst) => (
                          <InstitutionRow key={(inst as unknown as InstitutionTableEntry).institution_id} institution={inst as unknown as InstitutionTableEntry} />
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                {institutionTable && institutionTable.pages > 1 && (
                  <div className="flex items-center justify-between px-4 py-3 border-t">
                    <span className="text-xs text-gray-400">
                      {institutionTable.total} total institutions
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={institutionPage <= 1}
                        onClick={() => setInstitutionPage((p) => p - 1)}
                      >
                        Prev
                      </Button>
                      <span className="text-xs text-gray-500 self-center">
                        {institutionPage} / {institutionTable.pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={institutionPage >= institutionTable.pages}
                        onClick={() => setInstitutionPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
