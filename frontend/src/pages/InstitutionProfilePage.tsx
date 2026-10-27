import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getInstitution,
  getInstitutionCases,
  getInstitutionProfile,
  getInstitutionGraph,
} from "@/api/institutions";
import { getOverlaps } from "@/api/overlaps";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatusBadge, OverlapStatusBadge } from "@/components/shared/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Building2,
  Edit,
  MapPin,
  Phone,
  Mail,
  Globe,
  FileText,
  Briefcase,
  AlertTriangle,
  GitMerge,
  ExternalLink,
  Users,
  Clock,
  CheckCircle,
  ArrowUpRight,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, color }: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className={`rounded-lg p-4 ${color}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4" />
        <p className="text-xs font-medium uppercase tracking-wide">{label}</p>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

// ── Overview tab ──────────────────────────────────────────────────────────────

function OverviewTab({ id }: { id: string }) {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["institution-profile", id],
    queryFn: () => getInstitutionProfile(id),
  });

  const { data: institution } = useQuery({
    queryKey: ["institution", id],
    queryFn: () => getInstitution(id),
  });

  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (!institution) return null;

  const bureauBarData = (profile?.bureau_breakdown ?? []).map((b) => ({
    name: b.bureau_code,
    total: b.total_cases,
    active: b.active_cases,
    disposed: b.disposed_cases,
  }));

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Total Complaints" value={profile?.total_complaints ?? 0} icon={FileText} color="bg-blue-50 text-blue-800" />
        <StatCard label="Total Cases" value={profile?.total_cases ?? 0} icon={Briefcase} color="bg-indigo-50 text-indigo-800" />
        <StatCard label="Active Cases" value={profile?.active_cases ?? 0} icon={Clock} color="bg-purple-50 text-purple-800" />
        <StatCard label="Overdue Cases" value={profile?.overdue_cases ?? 0} icon={AlertTriangle} color="bg-red-50 text-red-800" />
        <StatCard label="Overlap Alerts" value={profile?.unresolved_overlap_alerts ?? 0} icon={GitMerge} color="bg-amber-50 text-amber-800" />
      </div>

      {/* Status counts */}
      <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
        <StatCard label="Pending" value={profile?.pending_cases ?? 0} icon={Clock} color="bg-yellow-50 text-yellow-800" />
        <StatCard label="Under Process" value={profile?.under_process_cases ?? 0} icon={Briefcase} color="bg-cyan-50 text-cyan-800" />
        <StatCard label="Transferred" value={profile?.transferred_cases ?? 0} icon={ArrowUpRight} color="bg-teal-50 text-teal-800" />
        <StatCard label="Disposed" value={profile?.disposed_cases ?? 0} icon={CheckCircle} color="bg-green-50 text-green-800" />
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Contact info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Building2 className="h-4 w-4 text-gray-400" />
              Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-400 font-medium uppercase">Type</p>
                <p className="text-gray-900">{institution.institution_type ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 font-medium uppercase">Status</p>
                <Badge variant={institution.is_active ? "success" : "secondary"}>
                  {institution.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            </div>
            {institution.address && (
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-gray-900">{institution.address}</p>
                  <p className="text-gray-500">
                    {[institution.city, institution.district, institution.state].filter(Boolean).join(", ")}
                  </p>
                </div>
              </div>
            )}
            {institution.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-gray-400" />
                <span className="text-gray-900">{institution.phone}</span>
              </div>
            )}
            {institution.email && (
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-gray-400" />
                <a href={`mailto:${institution.email}`} className="text-indigo-600 hover:underline">
                  {institution.email}
                </a>
              </div>
            )}
            {institution.website && (
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-gray-400" />
                <a href={institution.website} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                  {institution.website}
                </a>
              </div>
            )}
            <p className="text-xs text-gray-400 pt-1">
              Record created: {formatDate(institution.created_at)} · Last updated: {formatDate(institution.updated_at)}
            </p>
          </CardContent>
        </Card>

        {/* Bureau distribution chart */}
        {bureauBarData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Cases by Bureau</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={bureauBarData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="total" name="Total" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="active" name="Active" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="disposed" name="Disposed" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Assigned officers */}
      {(profile?.assigned_officers ?? []).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4 text-gray-400" />
              Assigned Officers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {profile!.assigned_officers.map((officer) => (
                <div key={officer.officer_id} className="py-2 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{officer.officer_name}</p>
                    <p className="text-xs text-gray-400">{officer.officer_email}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{officer.bureau_name ?? "—"}</p>
                    <p className="text-xs text-indigo-600">{officer.case_ids.length} case(s)</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Case history tab ───────────────────────────────────────────────────────────

function CaseHistoryTab({ id }: { id: string }) {
  const { data: profile, isLoading } = useQuery({
    queryKey: ["institution-profile", id],
    queryFn: () => getInstitutionProfile(id),
  });

  if (isLoading) return <Skeleton className="h-32 w-full" />;

  const history = profile?.case_history ?? [];

  if (history.length === 0) {
    return <p className="text-sm text-gray-400 text-center py-8">No cases found for this institution.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="bg-gray-50 border-b">
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Case #</th>
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Subject</th>
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Bureau</th>
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Status</th>
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Deadline</th>
            <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Created</th>
            <th className="py-3 px-4 w-8"></th>
          </tr>
        </thead>
        <tbody>
          {history.map((c) => {
            const isOverdue = c.expected_disposal_date &&
              new Date(c.expected_disposal_date) < new Date() &&
              c.status !== "disposed" && c.status !== "closed";
            return (
              <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                <td className="py-3 px-4 font-mono text-indigo-700 font-medium">{c.case_number}</td>
                <td className="py-3 px-4 text-gray-700 max-w-xs truncate">{c.subject}</td>
                <td className="py-3 px-4 text-gray-500 text-xs">{c.bureau_name ?? "—"}</td>
                <td className="py-3 px-4">
                  <StatusBadge status={c.status as any} />
                </td>
                <td className="py-3 px-4 text-xs">
                  {c.expected_disposal_date ? (
                    <span className={isOverdue ? "text-red-600 font-semibold" : "text-gray-500"}>
                      {c.expected_disposal_date}
                      {isOverdue && " ⚠"}
                    </span>
                  ) : "—"}
                </td>
                <td className="py-3 px-4 text-xs text-gray-400">{formatDate(c.created_at)}</td>
                <td className="py-3 px-4">
                  <Link to={`/cases/${c.id}`}>
                    <ExternalLink className="h-4 w-4 text-indigo-400" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Cases tab (paginated API) ─────────────────────────────────────────────────

function CasesTab({ id }: { id: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["institution-cases", id, page],
    queryFn: () => getInstitutionCases(id, { page, size: 15 }),
  });

  return (
    <div className="space-y-4">
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
        </div>
      ) : data?.items.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-8">No cases found for this institution.</p>
      ) : (
        <>
          <div className="space-y-2">
            {data?.items.map((c) => (
              <Link
                key={c.id}
                to={`/cases/${c.id}`}
                className="flex items-center justify-between rounded-lg border border-gray-100 p-3 hover:bg-gray-50 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium text-indigo-700">{c.case_number}</span>
                    <Badge variant="outline" className="text-xs">{c.bureau?.code ?? "—"}</Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{c.subject}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={c.status} />
                  <ExternalLink className="h-4 w-4 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <p className="text-xs text-gray-400">{data.total} total cases</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
                <span className="text-xs text-gray-500 self-center">{page} / {data.pages}</span>
                <Button variant="outline" size="sm" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Overlaps tab ──────────────────────────────────────────────────────────────

function OverlapsTab({ id }: { id: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["overlaps", { institution_id: id }],
    queryFn: () => getOverlaps({ size: 20 }),
  });
  const overlaps = data?.items ?? [];
  if (isLoading) return <Skeleton className="h-32 w-full" />;
  if (overlaps.length === 0) return <p className="text-sm text-gray-400 text-center py-8">No overlap alerts for this institution.</p>;
  return (
    <div className="space-y-2">
      {overlaps.map((alert) => (
        <Link
          key={alert.id}
          to={`/overlaps/${alert.id}`}
          className="flex items-center justify-between rounded-lg border border-amber-100 bg-amber-50 p-3 hover:bg-amber-100 transition-colors"
        >
          <div>
            <div className="flex items-center gap-2">
              <GitMerge className="h-4 w-4 text-amber-600" />
              <span className="font-medium text-amber-800 text-sm">{alert.alert_number}</span>
              <Badge variant="secondary" className="text-xs capitalize">{alert.match_type.replace(/_/g, " ")}</Badge>
            </div>
            {alert.detection_method && (
              <p className="text-xs text-amber-600 mt-0.5">Method: {alert.detection_method.replace(/_/g, " ")}</p>
            )}
            {alert.match_reasons && alert.match_reasons.length > 0 && (
              <p className="text-xs text-amber-700 mt-0.5 line-clamp-1">{alert.match_reasons[0]}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <OverlapStatusBadge status={alert.status} />
            <ExternalLink className="h-4 w-4 text-amber-500" />
          </div>
        </Link>
      ))}
    </div>
  );
}

// ── Graph tab ─────────────────────────────────────────────────────────────────

function GraphTab({ id }: { id: string }) {
  const { data: graph, isLoading } = useQuery({
    queryKey: ["institution-graph", id],
    queryFn: () => getInstitutionGraph(id),
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!graph || graph.nodes.length === 0) {
    return <p className="text-sm text-gray-400 text-center py-8">No relationship data available.</p>;
  }

  // Simple table-based fallback if ReactFlow is not installed yet
  const nodeTypeColors: Record<string, string> = {
    institution: "bg-indigo-100 text-indigo-800",
    case: "bg-blue-100 text-blue-800",
    complaint: "bg-amber-100 text-amber-800",
    bureau: "bg-purple-100 text-purple-800",
  };

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-400">Showing {graph.nodes.length} nodes and {graph.edges.length} relationships.</p>
      <div className="grid gap-2 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4">
        {graph.nodes.map((node) => (
          <div
            key={node.id}
            className={`rounded-lg p-3 ${nodeTypeColors[node.node_type] ?? "bg-gray-100 text-gray-700"}`}
          >
            <p className="text-xs font-semibold uppercase tracking-wide mb-1 opacity-60">{node.node_type}</p>
            <p className="text-sm font-medium leading-tight">{node.label}</p>
            {node.status && (
              <p className="text-xs opacity-70 mt-0.5 capitalize">{node.status.replace(/_/g, " ")}</p>
            )}
            {node.url && (
              <Link to={node.url} className="text-xs underline opacity-70 mt-1 block">
                View →
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Aliases tab ───────────────────────────────────────────────────────────────

function AliasesTab({ id }: { id: string }) {
  const { data: institution } = useQuery({
    queryKey: ["institution", id],
    queryFn: () => getInstitution(id),
  });
  const aliases = (institution as any)?.aliases ?? [];
  if (aliases.length === 0) {
    return <p className="text-sm text-gray-400 text-center py-8">No aliases registered for this institution.</p>;
  }
  return (
    <div className="space-y-2">
      {aliases.map((alias: any) => (
        <div key={alias.id} className="flex items-center justify-between rounded border border-gray-100 p-3">
          <div>
            <p className="text-sm font-medium text-gray-900">{alias.alias}</p>
            <p className="text-xs text-gray-400">{alias.alias_type?.replace(/_/g, " ")}</p>
          </div>
          <Badge variant="secondary" className="capitalize text-xs">{alias.alias_type?.replace(/_/g, " ")}</Badge>
        </div>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function InstitutionProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: institution, isLoading } = useQuery({
    queryKey: ["institution", id],
    queryFn: () => getInstitution(id!),
    enabled: !!id,
  });

  const { data: profile } = useQuery({
    queryKey: ["institution-profile", id],
    queryFn: () => getInstitutionProfile(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!institution) {
    return <div className="p-6 text-gray-500">Institution not found.</div>;
  }

  return (
    <div>
      <PageHeader
        title={institution.name}
        subtitle={institution.permanent_id ? `AICTE ID: ${institution.permanent_id}` : "No AICTE Permanent ID registered"}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Institutions", href: "/institutions" },
          { label: institution.name },
        ]}
        actions={
          <div className="flex gap-2">
            <Badge variant={institution.is_active ? "success" : "secondary"} className="self-center">
              {institution.is_active ? "Active" : "Inactive"}
            </Badge>
            <Button variant="outline" onClick={() => navigate(`/institutions/${id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </div>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="overview">
          <TabsList className="mb-6 flex-wrap">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="history">
              Case History
              {(profile?.total_cases ?? 0) > 0 && (
                <span className="ml-1.5 rounded-full bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5">
                  {profile?.total_cases}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="cases">Live Cases</TabsTrigger>
            <TabsTrigger value="overlaps">
              Overlap Alerts
              {(profile?.unresolved_overlap_alerts ?? 0) > 0 && (
                <span className="ml-1.5 rounded-full bg-amber-100 text-amber-700 text-xs px-1.5 py-0.5">
                  {profile?.unresolved_overlap_alerts}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="graph">Relationship Graph</TabsTrigger>
            <TabsTrigger value="aliases">Aliases</TabsTrigger>
          </TabsList>

          <TabsContent value="overview"><OverviewTab id={id!} /></TabsContent>
          <TabsContent value="history"><CaseHistoryTab id={id!} /></TabsContent>
          <TabsContent value="cases"><CasesTab id={id!} /></TabsContent>
          <TabsContent value="overlaps"><OverlapsTab id={id!} /></TabsContent>
          <TabsContent value="graph"><GraphTab id={id!} /></TabsContent>
          <TabsContent value="aliases"><AliasesTab id={id!} /></TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
