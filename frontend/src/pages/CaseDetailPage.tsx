import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCase,
  updateCaseStatus,
  assignCase,
  transferCase,
  addCaseAction,
  getRelatedCases,
} from "@/api/cases";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/shared/StatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "@/hooks/use-toast";
import { formatDate, formatDateTime, formatStatus } from "@/lib/utils";
import {
  ArrowLeft,
  Clock,
  User,
  Building2,
  AlertTriangle,
  MessageSquare,
  RefreshCw,
  UserCog,
  ArrowRightLeft,
  ArrowUpRight,
  FileText,
  Link2,
  Calendar,
} from "lucide-react";
import type { CaseStatus, RelatedCase } from "@/types";

// ── Valid status transitions ───────────────────────────────────────────────────

const TRANSITIONS: Record<CaseStatus, CaseStatus[]> = {
  open: ["pending_assignment", "under_process"],
  pending_assignment: ["under_process", "awaiting_information"],
  under_process: ["awaiting_information", "escalated", "transferred", "disposed", "closed"],
  awaiting_information: ["under_process", "escalated", "transferred", "disposed"],
  transferred: ["under_process", "escalated"],
  escalated: ["under_process", "disposed"],
  disposed: ["closed"],
  closed: [],
};

// ── SLA Progress Bar ──────────────────────────────────────────────────────────

function SLACard({ slaDeadline, isOverdue }: { slaDeadline: string | null; isOverdue: boolean }) {
  if (!slaDeadline)
    return (
      <Card>
        <CardContent className="p-4 text-center text-sm text-gray-400">No SLA deadline set</CardContent>
      </Card>
    );

  const deadline = new Date(slaDeadline);
  const now = new Date();
  const diffMs = deadline.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  const pct = isOverdue ? 100 : Math.max(0, Math.min(100, 100 - (diffDays / 30) * 100));

  return (
    <Card className={isOverdue ? "border-red-200" : ""}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Calendar className="h-4 w-4 text-gray-400" />
          SLA Deadline
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className={`text-lg font-bold ${isOverdue ? "text-red-600" : "text-gray-900"}`}>
          {isOverdue && <AlertTriangle className="inline h-4 w-4 mr-1" />}
          {formatDate(slaDeadline)}
        </p>
        <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${isOverdue ? "bg-red-500" : pct > 80 ? "bg-amber-500" : "bg-green-500"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-gray-500">
          {isOverdue
            ? `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) !== 1 ? "s" : ""}`
            : `${diffDays} day${diffDays !== 1 ? "s" : ""} remaining`}
        </p>
      </CardContent>
    </Card>
  );
}

// ── Action type icon ──────────────────────────────────────────────────────────

function ActionIcon({ type }: { type: string }) {
  if (type.includes("assign")) return <UserCog className="h-4 w-4 text-blue-500" />;
  if (type.includes("status")) return <RefreshCw className="h-4 w-4 text-indigo-500" />;
  if (type.includes("transfer")) return <ArrowRightLeft className="h-4 w-4 text-cyan-500" />;
  if (type.includes("escalat")) return <ArrowUpRight className="h-4 w-4 text-orange-500" />;
  if (type.includes("remark") || type.includes("comment")) return <MessageSquare className="h-4 w-4 text-gray-400" />;
  if (type.includes("document")) return <FileText className="h-4 w-4 text-purple-500" />;
  return <Clock className="h-4 w-4 text-gray-400" />;
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Modal state
  const [remarkOpen, setRemarkOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);

  // Form state
  const [remarkText, setRemarkText] = useState("");
  const [newStatus, setNewStatus] = useState<CaseStatus | "">("");
  const [statusRemarks, setStatusRemarks] = useState("");
  const [officerId, setOfficerId] = useState("");
  const [assignNotes, setAssignNotes] = useState("");
  const [transferBureau, setTransferBureau] = useState("");
  const [transferReason, setTransferReason] = useState("");

  const { data: caseData, isLoading } = useQuery({
    queryKey: ["case", id],
    queryFn: () => getCase(id!),
    enabled: !!id,
  });

  const { data: relatedCases } = useQuery({
    queryKey: ["case-related", id],
    queryFn: () => getRelatedCases(id!),
    enabled: !!id,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["case", id] });
    queryClient.invalidateQueries({ queryKey: ["cases"] });
  };

  const remarkMutation = useMutation({
    mutationFn: () =>
      addCaseAction(id!, {
        action_type: "remark",
        description: remarkText,
      }),
    onSuccess: () => {
      invalidate();
      toast({ title: "Remark added" });
      setRemarkText("");
      setRemarkOpen(false);
    },
    onError: (err: Error) => toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const statusMutation = useMutation({
    mutationFn: () => updateCaseStatus(id!, newStatus as CaseStatus, statusRemarks),
    onSuccess: () => {
      invalidate();
      toast({ title: "Status updated" });
      setNewStatus("");
      setStatusRemarks("");
      setStatusOpen(false);
    },
    onError: (err: Error) => toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const assignMutation = useMutation({
    mutationFn: () => assignCase(id!, officerId, assignNotes),
    onSuccess: () => {
      invalidate();
      toast({ title: "Case assigned" });
      setOfficerId("");
      setAssignNotes("");
      setAssignOpen(false);
    },
    onError: (err: Error) => toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const transferMutation = useMutation({
    mutationFn: () => transferCase(id!, transferBureau, transferReason),
    onSuccess: () => {
      invalidate();
      toast({ title: "Case transferred" });
      setTransferBureau("");
      setTransferReason("");
      setTransferOpen(false);
    },
    onError: (err: Error) => toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  if (isLoading)
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );

  if (!caseData) return <div className="p-6 text-gray-500">Case not found.</div>;

  const validTransitions = TRANSITIONS[caseData.status] ?? [];
  const isTerminal = caseData.status === "disposed" || caseData.status === "closed";

  return (
    <div>
      <PageHeader
        title={caseData.case_number}
        subtitle={caseData.subject}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Cases", href: "/cases" },
          { label: caseData.case_number },
        ]}
        actions={
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Status overview row */}
        <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Status</p>
            <StatusBadge status={caseData.status} />
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Priority</p>
            <PriorityBadge priority={caseData.priority} />
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Bureau</p>
            <p className="text-sm font-semibold text-gray-900">{caseData.bureau?.name ?? "—"}</p>
            <p className="text-xs text-gray-400">{caseData.bureau?.code ?? "—"}</p>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Category</p>
            <p className="text-sm font-medium text-gray-700">{caseData.category?.name ?? "—"}</p>
          </div>
        </div>

        {/* Action buttons */}
        {!isTerminal && (
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => setRemarkOpen(true)}>
              <MessageSquare className="mr-2 h-3.5 w-3.5" />
              Add Remark
            </Button>
            {validTransitions.length > 0 && (
              <Button variant="outline" size="sm" onClick={() => setStatusOpen(true)}>
                <RefreshCw className="mr-2 h-3.5 w-3.5" />
                Update Status
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => setAssignOpen(true)}>
              <UserCog className="mr-2 h-3.5 w-3.5" />
              Assign / Reassign
            </Button>
            <Button variant="outline" size="sm" onClick={() => setTransferOpen(true)}>
              <ArrowRightLeft className="mr-2 h-3.5 w-3.5" />
              Transfer
            </Button>
          </div>
        )}

        {/* Two-column layout */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Left: case details */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Case Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {caseData.institution_id && (
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-gray-400 shrink-0" />
                    <span className="text-gray-500">Institution ID:</span>
                    <Link
                      to={`/institutions/${caseData.institution_id}`}
                      className="font-medium text-indigo-600 hover:underline font-mono text-xs"
                    >
                      {caseData.institution_id.slice(0, 8)}…
                    </Link>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400 shrink-0" />
                  <span className="text-gray-500">Assigned Officer:</span>
                  <span className="font-medium">
                    {caseData.assigned_officer?.full_name ?? <Badge variant="secondary">Unassigned</Badge>}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400 shrink-0" />
                  <span className="text-gray-500">SLA Deadline:</span>
                  <span className="font-medium">
                    {caseData.expected_disposal_date ? formatDate(caseData.expected_disposal_date) : "—"}
                  </span>
                </div>
                <div className="border-t pt-4">
                  <p className="text-gray-500 mb-2 font-medium">Description</p>
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {caseData.description}
                  </p>
                </div>
                <div className="border-t pt-3 text-xs text-gray-400">
                  Created on {formatDateTime(caseData.created_at)}
                </div>
              </CardContent>
            </Card>

            {/* Action Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Action Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                {(caseData.recent_actions ?? []).length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-4">
                    No actions recorded yet.
                  </p>
                ) : (
                  <div className="relative space-y-0">
                    {(caseData.recent_actions ?? []).map((action, idx) => (
                      <div key={action.id} className="flex gap-4 pb-6 last:pb-0">
                        <div className="flex flex-col items-center">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white border-2 border-gray-200">
                            <ActionIcon type={action.action_type} />
                          </div>
                          {idx < (caseData.recent_actions ?? []).length - 1 && (
                            <div className="mt-1 flex-1 w-px bg-gray-200" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0 pb-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-sm font-medium text-gray-900 capitalize">
                              {formatStatus(action.action_type)}
                            </span>
                            <span className="text-xs text-gray-400 shrink-0">
                              {formatDateTime(action.performed_at)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-0.5">{action.description}</p>
                          {action.remarks && (
                            <p className="text-xs text-gray-400 mt-0.5 italic">
                              "{action.remarks}"
                            </p>
                          )}
                          {action.previous_status && action.new_status && (
                            <div className="flex items-center gap-2 mt-1">
                              <StatusBadge status={action.previous_status} />
                              <ArrowRightLeft className="h-3 w-3 text-gray-400" />
                              <StatusBadge status={action.new_status} />
                            </div>
                          )}
                          <p className="text-xs text-gray-400 mt-0.5">
                            by {(action.performed_by as { full_name?: string } | null)?.full_name ?? "—"}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Related Cases */}
            {relatedCases && relatedCases.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Link2 className="h-4 w-4 text-gray-400" />
                    Related Cases
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {relatedCases.map((rc: RelatedCase) => (
                      <div
                        key={rc.id}
                        className="flex items-center justify-between rounded border border-gray-100 p-3 hover:bg-gray-50"
                      >
                        <div>
                          <span className="font-mono text-sm font-medium text-indigo-700">
                            {rc.related_case_id}
                          </span>
                          <p className="text-xs text-gray-500 capitalize">
                            {rc.relationship_type.replace(/_/g, " ")}
                          </p>
                          {rc.rationale && (
                            <p className="text-xs text-gray-400 mt-0.5">{rc.rationale}</p>
                          )}
                        </div>
                        <Link
                          to={`/cases/${rc.related_case_id}`}
                          className="text-xs text-indigo-600 hover:underline flex items-center gap-1"
                        >
                          View <ArrowUpRight className="h-3 w-3" />
                        </Link>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right sidebar */}
          <div className="space-y-6">
            <SLACard
              slaDeadline={caseData.expected_disposal_date}
              isOverdue={!!caseData.expected_disposal_date && new Date(caseData.expected_disposal_date) < new Date() && caseData.status !== "disposed" && caseData.status !== "closed"}
            />

            {/* Institution card */}
            {caseData.institution_id && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Institution</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  <Link
                    to={`/institutions/${caseData.institution_id}`}
                    className="font-medium text-indigo-600 hover:underline block font-mono text-xs"
                  >
                    View Institution →
                  </Link>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Add Remark Modal */}
      <Dialog open={remarkOpen} onOpenChange={setRemarkOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Remark</DialogTitle>
          </DialogHeader>
          <Textarea
            value={remarkText}
            onChange={(e) => setRemarkText(e.target.value)}
            placeholder="Enter your remark..."
            rows={4}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemarkOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => remarkMutation.mutate()}
              disabled={!remarkText.trim() || remarkMutation.isPending}
              isLoading={remarkMutation.isPending}
            >
              Add Remark
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Update Status Modal */}
      <Dialog open={statusOpen} onOpenChange={setStatusOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Case Status</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Current status: <StatusBadge status={caseData.status} />
              </label>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                New Status *
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as CaseStatus)}
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Select new status...</option>
                {validTransitions.map((s) => (
                  <option key={s} value={s}>
                    {formatStatus(s)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Remarks
              </label>
              <Textarea
                value={statusRemarks}
                onChange={(e) => setStatusRemarks(e.target.value)}
                placeholder="Reason for status change..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => statusMutation.mutate()}
              disabled={!newStatus || statusMutation.isPending}
              isLoading={statusMutation.isPending}
            >
              Update Status
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Modal */}
      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign / Reassign Officer</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Officer ID *
              </label>
              <input
                type="text"
                value={officerId}
                onChange={(e) => setOfficerId(e.target.value)}
                placeholder="Enter officer user ID"
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Notes
              </label>
              <Textarea
                value={assignNotes}
                onChange={(e) => setAssignNotes(e.target.value)}
                placeholder="Assignment notes..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => assignMutation.mutate()}
              disabled={!officerId.trim() || assignMutation.isPending}
              isLoading={assignMutation.isPending}
            >
              Assign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transfer Modal */}
      <Dialog open={transferOpen} onOpenChange={setTransferOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Transfer Case</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Destination Bureau ID *
              </label>
              <input
                type="text"
                value={transferBureau}
                onChange={(e) => setTransferBureau(e.target.value)}
                placeholder="Enter bureau UUID"
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Reason *
              </label>
              <Textarea
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                placeholder="Reason for transfer..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTransferOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => transferMutation.mutate()}
              disabled={!transferBureau.trim() || !transferReason.trim() || transferMutation.isPending}
              isLoading={transferMutation.isPending}
            >
              Transfer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
