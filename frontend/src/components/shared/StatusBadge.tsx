import { Badge } from "@/components/ui/badge";
import type { BadgeProps } from "@/components/ui/badge";
import type { ComplaintStatus, CaseStatus, OverlapStatus, Priority } from "@/types";
import { formatStatus } from "@/lib/utils";

// ── Complaint / Case status badge ─────────────────────────────────────────────

const statusVariantMap: Record<
  ComplaintStatus | CaseStatus,
  BadgeProps["variant"]
> = {
  received: "info",
  pending_assignment: "warning",
  under_process: "info",
  awaiting_information: "warning",
  transferred: "secondary",
  escalated: "destructive",
  disposed: "success",
  closed: "secondary",
  open: "info",
};

interface StatusBadgeProps {
  status: ComplaintStatus | CaseStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variant = statusVariantMap[status] ?? "secondary";
  return <Badge variant={variant}>{formatStatus(status)}</Badge>;
}

// ── Priority badge ────────────────────────────────────────────────────────────

const priorityVariantMap: Record<Priority, BadgeProps["variant"]> = {
  low: "secondary",
  medium: "info",
  high: "warning",
  critical: "destructive",
};

interface PriorityBadgeProps {
  priority: Priority;
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const variant = priorityVariantMap[priority] ?? "secondary";
  return (
    <Badge variant={variant}>
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </Badge>
  );
}

// ── Overlap status badge ──────────────────────────────────────────────────────

const overlapVariantMap: Record<OverlapStatus, BadgeProps["variant"]> = {
  pending_review: "warning",
  confirmed_related: "info",
  false_positive: "secondary",
  separate_handling: "success",
};

interface OverlapStatusBadgeProps {
  status: OverlapStatus;
}

export function OverlapStatusBadge({ status }: OverlapStatusBadgeProps) {
  const variant = overlapVariantMap[status] ?? "secondary";
  return <Badge variant={variant}>{formatStatus(status)}</Badge>;
}
