import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getConflict, reviewConflict } from "@/api/conflicts";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, Building2, Briefcase, CheckCircle, X } from "lucide-react";
import type { ConflictSeverity, ConflictStatus } from "@/types";
import { formatDate } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

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
  multi_bureau_same_issue: "Multiple Bureaus — Same Institution Active Cases",
  overlapping_officer_actions: "Overlapping Officer Actions",
  competing_deadlines: "Competing Deadlines",
  transfer_while_related_active: "Transfer While Related Case Active",
};

export default function ConflictDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [resolutionNote, setResolutionNote] = useState("");

  const { data: alert, isLoading } = useQuery({
    queryKey: ["conflict", id],
    queryFn: () => getConflict(id!),
    enabled: !!id,
  });

  const { mutate: doReview, isPending } = useMutation({
    mutationFn: (action: "acknowledge" | "resolve" | "dismiss") =>
      reviewConflict(id!, { action, resolution_note: resolutionNote || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conflict", id] });
      queryClient.invalidateQueries({ queryKey: ["conflicts"] });
      toast({ title: "Action recorded", description: "Conflict alert updated." });
      setResolutionNote("");
    },
    onError: () => {
      toast({ title: "Error", description: "Could not update conflict alert.", variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!alert) {
    return <div className="p-6 text-gray-500">Conflict alert not found.</div>;
  }

  return (
    <div>
      <PageHeader
        title={RULE_LABELS[alert.rule_triggered] ?? alert.rule_triggered.replace(/_/g, " ")}
        subtitle={alert.institution_name ?? "Unknown Institution"}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Conflicts", href: "/conflicts" },
          { label: "Detail" },
        ]}
        actions={
          <div className="flex gap-2">
            <Badge className={SEVERITY_COLORS[alert.severity]}>{alert.severity} severity</Badge>
            <Badge className={STATUS_COLORS[alert.status]}>{alert.status}</Badge>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Summary card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Coordination Issue
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {alert.institution_name && (
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-700">{alert.institution_name}</span>
                {alert.institution_id && (
                  <Link to={`/institutions/${alert.institution_id}`} className="text-xs text-indigo-600 hover:underline">
                    View Profile →
                  </Link>
                )}
              </div>
            )}

            <div>
              <p className="text-xs text-gray-400 uppercase font-semibold mb-1">Rule Triggered</p>
              <p className="text-sm text-gray-900">{RULE_LABELS[alert.rule_triggered] ?? alert.rule_triggered}</p>
            </div>

            {alert.rule_description && (
              <div>
                <p className="text-xs text-gray-400 uppercase font-semibold mb-1">Description</p>
                <p className="text-sm text-gray-700">{alert.rule_description}</p>
              </div>
            )}

            {alert.recommended_action && (
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
                <p className="text-xs font-semibold text-blue-700 uppercase mb-1">Recommended Action</p>
                <p className="text-sm text-blue-800">{alert.recommended_action}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-xs text-gray-400 uppercase font-semibold mb-1">Affected Cases</p>
                <div className="flex flex-wrap gap-1">
                  {(alert.case_ids ?? []).map((cid) => (
                    <Link key={cid} to={`/cases/${cid}`}>
                      <Badge variant="outline" className="text-xs font-mono">
                        <Briefcase className="h-3 w-3 mr-1" />{cid.slice(0, 8)}…
                      </Badge>
                    </Link>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase font-semibold mb-1">Involved Bureaus</p>
                <div className="flex flex-wrap gap-1">
                  {(alert.bureau_ids ?? []).map((bid) => (
                    <Badge key={bid} variant="secondary" className="text-xs">{bid.slice(0, 8)}…</Badge>
                  ))}
                </div>
              </div>
            </div>

            <p className="text-xs text-gray-400">Detected: {formatDate(alert.created_at)}</p>
          </CardContent>
        </Card>

        {/* Evidence */}
        {alert.evidence && Object.keys(alert.evidence).length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Evidence</CardTitle></CardHeader>
            <CardContent>
              <pre className="text-xs bg-gray-50 rounded p-3 overflow-auto max-h-48 text-gray-700">
                {JSON.stringify(alert.evidence, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Resolution info */}
        {alert.status === "resolved" || alert.status === "dismissed" ? (
          <Card>
            <CardHeader><CardTitle className="text-base">Resolution</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm text-gray-700">
              <p><span className="text-gray-400">Status:</span> {alert.status}</p>
              {alert.resolution_note && <p><span className="text-gray-400">Note:</span> {alert.resolution_note}</p>}
              {alert.resolved_at && <p><span className="text-gray-400">Resolved at:</span> {formatDate(alert.resolved_at)}</p>}
            </CardContent>
          </Card>
        ) : (
          /* Review actions */
          <Card>
            <CardHeader><CardTitle className="text-base">Review Actions</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 uppercase font-semibold">Resolution Note (optional)</label>
                <textarea
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  className="mt-1 w-full rounded border border-gray-300 text-sm p-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
                  rows={3}
                  placeholder="Add a note about this coordination issue..."
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {alert.status === "open" && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={isPending}
                    onClick={() => doReview("acknowledge")}
                  >
                    <CheckCircle className="mr-2 h-4 w-4 text-amber-500" />
                    Acknowledge
                  </Button>
                )}
                <Button
                  size="sm"
                  disabled={isPending}
                  onClick={() => doReview("resolve")}
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Mark Resolved
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isPending}
                  onClick={() => doReview("dismiss")}
                >
                  <X className="mr-2 h-4 w-4 text-gray-500" />
                  Dismiss
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
