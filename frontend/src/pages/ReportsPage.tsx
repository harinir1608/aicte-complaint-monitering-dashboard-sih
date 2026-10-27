import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { Download, Filter } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// ── Export helper ─────────────────────────────────────────────────────────────

async function downloadReport(
  endpoint: string,
  filename: string,
  params: object = {}
) {
  try {
    const response = await apiClient.get(endpoint, {
      params: { ...params, format: "csv" },
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    toast({ title: "Export failed", description: (err as Error).message, variant: "destructive" });
  }
}

// ── Date range filter ─────────────────────────────────────────────────────────

interface DateFilter {
  date_from: string;
  date_to: string;
  bureau_id: string;
}

function DateFilterBar({
  value,
  onChange,
}: {
  value: DateFilter;
  onChange: (v: DateFilter) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3 items-end">
      <Filter className="h-4 w-4 text-gray-400 self-center" />
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">From</label>
        <input
          type="date"
          value={value.date_from}
          onChange={(e) => onChange({ ...value, date_from: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500 font-medium">To</label>
        <input
          type="date"
          value={value.date_to}
          onChange={(e) => onChange({ ...value, date_to: e.target.value })}
          className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  );
}

// ── Institution-wise tab ──────────────────────────────────────────────────────

interface InstitutionRow {
  id: string;
  name: string;
  total_complaints: number;
  active_cases: number;
  disposed_cases: number;
  overdue_cases: number;
  state: string | null;
}

const institutionColumns: ColumnDef<InstitutionRow>[] = [
  { key: "name", header: "Institution", cell: (row) => <span className="font-medium">{row.name}</span> },
  { key: "state", header: "State", cell: (row) => row.state ?? "—" },
  { key: "total_complaints", header: "Total Complaints", sortable: true, cell: (row) => <span className="font-semibold">{row.total_complaints}</span> },
  { key: "active_cases", header: "Active Cases", sortable: true, cell: (row) => <span className="text-blue-700 font-semibold">{row.active_cases}</span> },
  { key: "disposed_cases", header: "Disposed", sortable: true, cell: (row) => <span className="text-green-700">{row.disposed_cases}</span> },
  { key: "overdue_cases", header: "Overdue", sortable: true, cell: (row) => <span className={row.overdue_cases > 0 ? "text-red-600 font-semibold" : "text-gray-500"}>{row.overdue_cases}</span> },
];

function InstitutionTab() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({ date_from: "", date_to: "", bureau_id: "" });
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["report-institutions", dateFilter, page],
    queryFn: async () => {
      const response = await apiClient.get<{ items: InstitutionRow[]; total: number; pages: number; page: number; size: number; page_size: number }>("/reports/institutions", {
        params: { ...dateFilter, page, size: 20 },
      });
      return response.data;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <DateFilterBar value={dateFilter} onChange={setDateFilter} />
        <Button variant="outline" size="sm" onClick={() => downloadReport("/reports/institutions", "institution_report.csv", dateFilter)}>
          <Download className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>
      <DataTable
        columns={institutionColumns}
        data={data?.items ?? []}
        isLoading={isLoading}
        rowKey={(row) => row.id}
        emptyMessage="No institution data available."
        pagination={data ? { page: data.page, size: data.page_size, total: data.total, pages: data.pages } : undefined}
        onPageChange={setPage}
      />
    </div>
  );
}

// ── Ageing tab ────────────────────────────────────────────────────────────────

interface AgeingRow {
  bucket: string;
  count: number;
  bureau_breakdown?: Record<string, number>;
}

const ageingColumns: ColumnDef<AgeingRow>[] = [
  { key: "bucket", header: "Age Bucket", cell: (row) => <span className="font-medium">{row.bucket}</span> },
  { key: "count", header: "Case Count", sortable: true, cell: (row) => <span className="font-bold text-indigo-700">{row.count}</span> },
];

function AgeingTab() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({ date_from: "", date_to: "", bureau_id: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["report-ageing", dateFilter],
    queryFn: async () => {
      const response = await apiClient.get<AgeingRow[]>("/reports/ageing", { params: dateFilter });
      return response.data;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <DateFilterBar value={dateFilter} onChange={setDateFilter} />
        <Button variant="outline" size="sm" onClick={() => downloadReport("/reports/ageing", "ageing_report.csv", dateFilter)}>
          <Download className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Pending Cases by Age</CardTitle></CardHeader>
          <CardContent>
            {!data || data.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No ageing data available</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} name="Cases" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
        <DataTable
          columns={ageingColumns}
          data={data ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.bucket}
          emptyMessage="No data."
        />
      </div>
    </div>
  );
}

// ── Workload tab ──────────────────────────────────────────────────────────────

interface WorkloadRow {
  officer_name: string;
  bureau_code: string;
  assigned_cases: number;
  overdue_cases: number;
  disposed_cases: number;
}

const workloadColumns: ColumnDef<WorkloadRow>[] = [
  { key: "officer_name", header: "Officer", cell: (row) => <span className="font-medium">{row.officer_name}</span> },
  { key: "bureau_code", header: "Bureau", cell: (row) => row.bureau_code },
  { key: "assigned_cases", header: "Assigned Cases", sortable: true, cell: (row) => <span className="font-semibold">{row.assigned_cases}</span> },
  { key: "overdue_cases", header: "Overdue", sortable: true, cell: (row) => <span className={row.overdue_cases > 0 ? "text-red-600 font-semibold" : "text-gray-500"}>{row.overdue_cases}</span> },
  { key: "disposed_cases", header: "Disposed", sortable: true, cell: (row) => <span className="text-green-700">{row.disposed_cases}</span> },
];

function WorkloadTab() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({ date_from: "", date_to: "", bureau_id: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["report-workload", dateFilter],
    queryFn: async () => {
      const response = await apiClient.get<WorkloadRow[]>("/reports/workload", { params: dateFilter });
      return response.data;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <DateFilterBar value={dateFilter} onChange={setDateFilter} />
        <Button variant="outline" size="sm" onClick={() => downloadReport("/reports/workload", "workload_report.csv", dateFilter)}>
          <Download className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>
      {data && data.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Officer Workload Chart</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.slice(0, 12)} margin={{ top: 5, right: 20, left: 0, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="officer_name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="assigned_cases" name="Assigned" fill="#6366f1" radius={[3, 3, 0, 0]} />
                <Bar dataKey="overdue_cases" name="Overdue" fill="#ef4444" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
      <DataTable
        columns={workloadColumns}
        data={data ?? []}
        isLoading={isLoading}
        rowKey={(row) => row.officer_name}
        emptyMessage="No workload data available."
      />
    </div>
  );
}

// ── Overlaps tab ──────────────────────────────────────────────────────────────

interface OverlapReportRow {
  month: string;
  total_alerts: number;
  pending: number;
  confirmed_related: number;
  false_positive: number;
  separate_handling: number;
  false_positive_rate?: number;
}

const overlapReportColumns: ColumnDef<OverlapReportRow>[] = [
  { key: "month", header: "Month", cell: (row) => row.month },
  { key: "total_alerts", header: "Total Alerts", sortable: true, cell: (row) => <span className="font-semibold">{row.total_alerts}</span> },
  { key: "pending", header: "Pending", cell: (row) => row.pending },
  { key: "confirmed_related", header: "Confirmed", cell: (row) => <span className="text-blue-700">{row.confirmed_related}</span> },
  { key: "false_positive", header: "False Positive", cell: (row) => <span className="text-gray-500">{row.false_positive}</span> },
  {
    key: "false_positive_rate",
    header: "FP Rate",
    cell: (row) =>
      row.false_positive_rate !== undefined
        ? `${(row.false_positive_rate * 100).toFixed(1)}%`
        : "—",
  },
];

function OverlapsTab() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({ date_from: "", date_to: "", bureau_id: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["report-overlaps", dateFilter],
    queryFn: async () => {
      const response = await apiClient.get<OverlapReportRow[]>("/reports/overlaps", { params: dateFilter });
      return response.data;
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <DateFilterBar value={dateFilter} onChange={setDateFilter} />
        <Button variant="outline" size="sm" onClick={() => downloadReport("/reports/overlaps", "overlap_report.csv", dateFilter)}>
          <Download className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>
      {data && data.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Overlap Alert Trends</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="total_alerts" stroke="#f59e0b" name="Total Alerts" strokeWidth={2} />
                <Line type="monotone" dataKey="confirmed_related" stroke="#3b82f6" name="Confirmed" strokeWidth={2} />
                <Line type="monotone" dataKey="false_positive" stroke="#94a3b8" name="False Positive" strokeWidth={2} strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
      <DataTable
        columns={overlapReportColumns}
        data={data ?? []}
        isLoading={isLoading}
        rowKey={(row) => row.month}
        emptyMessage="No overlap report data available."
      />
    </div>
  );
}

// ── Trends tab ────────────────────────────────────────────────────────────────

interface TrendRow {
  month: string;
  complaints_received: number;
  cases_disposed: number;
  cases_escalated: number;
}

function TrendsTab() {
  const [dateFilter, setDateFilter] = useState<DateFilter>({ date_from: "", date_to: "", bureau_id: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["report-trends", dateFilter],
    queryFn: async () => {
      const response = await apiClient.get<TrendRow[]>("/dashboard/trends", { params: dateFilter });
      return response.data;
    },
  });

  const trendColumns: ColumnDef<TrendRow>[] = [
    { key: "month", header: "Month", cell: (row) => row.month },
    { key: "complaints_received", header: "Complaints Received", sortable: true, cell: (row) => <span className="font-semibold text-blue-700">{row.complaints_received}</span> },
    { key: "cases_disposed", header: "Cases Disposed", sortable: true, cell: (row) => <span className="font-semibold text-green-700">{row.cases_disposed}</span> },
    { key: "cases_escalated", header: "Cases Escalated", sortable: true, cell: (row) => <span className="font-semibold text-orange-600">{row.cases_escalated}</span> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <DateFilterBar value={dateFilter} onChange={setDateFilter} />
        <Button variant="outline" size="sm" onClick={() => downloadReport("/reports/trends", "trends_report.csv", dateFilter)}>
          <Download className="mr-2 h-4 w-4" /> Export CSV
        </Button>
      </div>
      {data && data.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Monthly Intake & Disposal Trends</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="complaints_received" stroke="#6366f1" name="Intake" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="cases_disposed" stroke="#22c55e" name="Disposed" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="cases_escalated" stroke="#f97316" name="Escalated" strokeWidth={2} strokeDasharray="4 2" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
      <DataTable
        columns={trendColumns}
        data={data ?? []}
        isLoading={isLoading}
        rowKey={(row) => row.month}
        emptyMessage="No trend data available."
      />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  return (
    <div>
      <PageHeader
        title="Reports & Analytics"
        subtitle="Data-driven reports and exportable analysis across all modules"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Reports" }]}
      />

      <div className="p-6">
        <Tabs defaultValue="institution">
          <TabsList className="mb-6">
            <TabsTrigger value="institution">Institution-wise</TabsTrigger>
            <TabsTrigger value="workload">Workload</TabsTrigger>
            <TabsTrigger value="ageing">Ageing</TabsTrigger>
            <TabsTrigger value="overlaps">Overlaps</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
          </TabsList>

          <TabsContent value="institution">
            <InstitutionTab />
          </TabsContent>
          <TabsContent value="workload">
            <WorkloadTab />
          </TabsContent>
          <TabsContent value="ageing">
            <AgeingTab />
          </TabsContent>
          <TabsContent value="overlaps">
            <OverlapsTab />
          </TabsContent>
          <TabsContent value="trends">
            <TrendsTab />
          </TabsContent>
        </Tabs>

        <div className="mt-6 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <p className="text-sm text-blue-800">
            All reports reflect live database records at the time of generation.
            Each exported CSV includes a generation timestamp. Apply filters before
            exporting to narrow the dataset.
          </p>
        </div>
      </div>
    </div>
  );
}
