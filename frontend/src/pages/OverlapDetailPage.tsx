import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOverlap, reviewOverlap } from "@/api/overlaps";
import { getCase } from "@/api/cases";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OverlapStatusBadge, StatusBadge, PriorityBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { ArrowLeft, GitMerge, Check, X, Minus, Info, ExternalLink, Building2 } from "lucide-react";
import { formatDate, formatDateTime } from "@/lib/utils";
import type { OverlapStatus } from "@/types";

// ── Case column ───────────────────────────────────────────────────────────────

function CaseColumn({ caseId, label }: { caseId: string; label: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => getCase(caseId),
    enabled: !!caseId,
  });

  return (
    <div className="flex-1 rounded-lg border bg-white p-5 space-y-3 min-w-0">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide">{label}</h3>
        {data && (
          <Link
            to={`/cases/${data.id}`}
            className="text-xs text-indigo-600 hover:underline flex items-center gap-1"
          >
            View full case <ExternalLink className="h-3 w-3" />
          </Link>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-40" />
        </div>
      ) : !data ? (
        <p className="text-sm text-gray-400">Case details unavailable</p>
      ) : (
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-mono text-sm font-bold text-indigo-700">
              {data.case_number}
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <StatusBadge status={data.status} />
            <PriorityBadge priority={data.priority} />
            {data.bureau && (
              <Badge variant="outline" className="text-xs">
                {data.bureau.code}
              </Badge>
            )}
          </div>

          <div>
            <p className="text-xs text-gray-400 font-medium uppercase">Subject</p>
            <p className="text-gray-800 font-medium line-clamp-2">{data.subject}</p>
          </div>

          <div>
            <p className="text-xs text-gray-400 font-medium uppercase">Description</p>
            <p className="text-gray-600 line-clamp-3 text-xs">{data.description}</p>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <div>
              <p className="text-xs text-gray-400">Category</p>
              <p className="text-xs font-medium text-gray-800">{data.category?.name ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Assigned To</p>
              <p className="text-xs font-medium text-gray-800">
                {data.assigned_officer?.full_name ?? "Unassigned"}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400">SLA Deadline</p>
              {(() => {
                const isOverdue = !!data.expected_disposal_date && new Date(data.expected_disposal_date) < new Date() && data.status !== "disposed" && data.status !== "closed";
                return (
                  <p className={`text-xs font-medium ${isOverdue ? "text-red-600" : "text-gray-800"}`}>
                    {data.expected_disposal_date ? formatDate(data.expected_disposal_date) : "—"}
                    {isOverdue && " (OVERDUE)"}
                  </p>
                );
              })()}
            </div>
          </div>

          {data.bureau && (
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-400 font-medium uppercase">Bureau</p>
              <p className="text-sm font-medium text-gray-800">
                {data.bureau.name} ({data.bureau.code})
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

const REVIEW_OPTIONS: {
  value: OverlapStatus;
  label: string;
  icon: React.ElementType;
  description: string;
}[] = [
  {
    value: "confirmed_related",
    label: "Confirmed Related",
    icon: Check,
    description: "Cases are confirmed to be related and require coordination",
  },
  {
    value: "false_positive",
    label: "False Positive",
    icon: X,
    description: "Cases are not related — alert is a false positive",
  },
  {
    value: "separate_handling",
    label: "Maintain Separate",
    icon: Minus,
    description: "Cases are related but should be handled independently",
  },
];

export default function OverlapDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [remarks, setRemarks] = useState("");
  const [decision, setDecision] = useState<OverlapStatus | null>(null);

  const { data: overlap, isLoading } = useQuery({
    queryKey: ["overlap", id],
    queryFn: () => getOverlap(id!),
    enabled: !!id,
  });

  const mutation = useMutation({
    mutationFn: () => reviewOverlap(id!, decision!, remarks),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["overlap", id] });
      queryClient.invalidateQueries({ queryKey: ["overlaps"] });
      toast({ title: "Review submitted successfully" });
      setDecision(null);
      setRemarks("");
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  if (isLoading)
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );

  if (!overlap) return <div className="p-6 text-gray-500">Alert not found.</div>;

  const isPendingReview = overlap.status === "pending_review";

  return (
    <div>
      <PageHeader
        title="Potential Overlapping Cases — Coordination Required"
        subtitle={`Alert: ${overlap.alert_number}`}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Overlap Review", href: "/overlaps" },
          { label: overlap.alert_number },
        ]}
        actions={
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Alert header */}
        <div className="flex items-center gap-4 rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
            <GitMerge className="h-5 w-5 text-amber-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-bold text-amber-800">{overlap.alert_number}</h2>
              <OverlapStatusBadge status={overlap.status} />
            </div>
            <p className="text-xs text-amber-700 mt-0.5">
              Created {formatDateTime(overlap.created_at)}
            </p>
          </div>
        </div>

        {/* Institution + Match info */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-4 w-4 text-gray-400" />
                Institution
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-1">
              {overlap.institution_id ? (
                <Link
                  to={`/institutions/${overlap.institution_id}`}
                  className="font-medium text-indigo-600 hover:underline text-base block"
                >
                  View Institution
                </Link>
              ) : (
                <p className="text-gray-500 italic">Institution not linked</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Match Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-gray-400 uppercase font-medium">Match Type</p>
                  <p className="mt-0.5 font-medium capitalize">
                    {overlap.match_type.replace(/_/g, " ")}
                  </p>
                </div>
                {overlap.match_score != null && (
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-medium">
                      Match Score
                    </p>
                    <p className="mt-0.5 text-2xl font-bold text-indigo-700">
                      {Number(overlap.match_score).toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {(overlap.bureaus_involved ?? []).map((_bureauId, i) => (
                  <Badge key={i} variant="secondary">
                    Bureau {i + 1}
                  </Badge>
                ))}
              </div>

              {overlap.match_evidence && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
                  <p className="text-xs font-medium text-amber-800 uppercase tracking-wide mb-1 flex items-center gap-1">
                    <Info className="h-3 w-3" /> Match Evidence
                  </p>
                  <pre className="text-xs text-amber-900 whitespace-pre-wrap">
                    {JSON.stringify(overlap.match_evidence, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Side-by-side case comparison */}
        <div>
          <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3">
            Case Comparison
          </h2>
          <div className="flex gap-4 flex-col lg:flex-row">
            {overlap.case_id_incoming ? (
              <CaseColumn caseId={overlap.case_id_incoming} label="Incoming Case" />
            ) : (
              <div className="flex-1 rounded-lg border bg-gray-50 p-5 text-center text-sm text-gray-400">
                No incoming case linked
              </div>
            )}

            {overlap.case_id_existing ? (
              <CaseColumn caseId={overlap.case_id_existing} label="Existing Case" />
            ) : (
              <div className="flex-1 rounded-lg border bg-gray-50 p-5 text-center text-sm text-gray-400">
                No existing case available
              </div>
            )}
          </div>
        </div>

        {/* Review form */}
        {isPendingReview ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Submit Review Decision</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {REVIEW_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setDecision(opt.value)}
                    className={`flex flex-col items-start gap-2 rounded-lg border-2 p-4 text-left transition-colors ${
                      decision === opt.value
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <opt.icon className="h-4 w-4" />
                      <span className="font-medium text-sm">{opt.label}</span>
                    </div>
                    <p className="text-xs text-gray-500">{opt.description}</p>
                  </button>
                ))}
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">
                  Review Remarks *
                </label>
                <Textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Provide detailed remarks explaining your review decision. This will be recorded in the audit trail."
                  rows={4}
                />
              </div>

              <div className="flex items-center gap-3">
                <Button
                  onClick={() => mutation.mutate()}
                  disabled={!decision || !remarks.trim() || mutation.isPending}
                  isLoading={mutation.isPending}
                >
                  Submit Review
                </Button>
                {decision && (
                  <p className="text-sm text-gray-500">
                    Decision:{" "}
                    <strong>{REVIEW_OPTIONS.find((o) => o.value === decision)?.label}</strong>
                  </p>
                )}
              </div>

              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-800">
                <strong>Important:</strong> Reviewing this alert will not automatically merge,
                close, or modify the related cases. Each case retains its independent status and
                history. Coordination notes can be added after review.
              </div>
            </CardContent>
          </Card>
        ) : (
          overlap.review && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Review Decision</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-4">
                <div className="flex items-center gap-3">
                  <span className="text-gray-500">Decision:</span>
                  <OverlapStatusBadge status={overlap.review.decision as OverlapStatus} />
                </div>
                {overlap.review.remarks && (
                  <div>
                    <p className="text-gray-500 mb-1 font-medium">Reviewer Remarks</p>
                    <p className="text-gray-700 bg-gray-50 rounded p-3 border">
                      {overlap.review.remarks}
                    </p>
                  </div>
                )}
                <p className="text-xs text-gray-400">
                  Reviewed by{" "}
                  <strong>{overlap.review.reviewed_by.full_name}</strong> on{" "}
                  {formatDateTime(overlap.review.reviewed_at)}
                </p>
              </CardContent>
            </Card>
          )
        )}
      </div>
    </div>
  );
}
