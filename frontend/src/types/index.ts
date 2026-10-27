// ─── Enum types ────────────────────────────────────────────────────────────────

export type ComplaintStatus =
  | "received"
  | "pending_assignment"
  | "under_process"
  | "awaiting_information"
  | "transferred"
  | "escalated"
  | "disposed"
  | "closed";

export type CaseStatus =
  | "open"
  | "pending_assignment"
  | "under_process"
  | "awaiting_information"
  | "transferred"
  | "escalated"
  | "disposed"
  | "closed";

export type OverlapStatus =
  | "pending_review"
  | "confirmed_related"
  | "false_positive"
  | "separate_handling";

export type Priority = "low" | "medium" | "high" | "critical";

export type MatchType =
  | "exact_id"
  | "same_institution"
  | "possible_institution"
  | "related_complaint"
  | "same_complaint_reference"
  | "no_match";

// ─── Core domain types ────────────────────────────────────────────────────────

// Role is a string enum from the API (not an object)
export type Role =
  | "system_admin"
  | "rb_officer"
  | "pgrc_officer"
  | "bureau_officer"
  | "regional_officer"
  | "senior_management";

export interface Bureau {
  id: string;
  name: string;
  code: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Region {
  id: string;
  name: string;
  code: string;
  states: string[];
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  employee_id: string | null;
  role: Role;
  bureau_id: string | null;
  region_id: string | null;
  bureau: Bureau | null;
  region: Region | null;
  is_active: boolean;
  is_superuser: boolean;
  last_login: string | null;
}

export interface InstitutionAlias {
  id: string;
  institution_id: string;
  alias: string;
  alias_type: "abbreviation" | "former_name" | "common_name" | "other";
  created_at: string;
}

// Matches actual /api/v1/institutions response
export interface Institution {
  id: string;
  permanent_id: string | null;   // API field name
  name: string;
  state: string | null;
  district: string | null;
  region_id: string | null;
  institution_type: string | null;
  address: string | null;
  city: string | null;
  pin_code: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Matches actual /api/v1/complaints response
export interface Complaint {
  id: string;
  complaint_number: string;
  institution_id: string | null;
  institution_name_raw: string | null;
  institution: { id: string; name: string; permanent_id: string | null } | null;
  source: string;
  category_id: string | null;
  category: { id: string; code: string; name: string } | null;
  subject: string;
  description: string;
  received_date: string;
  complainant_name: string | null;
  complainant_contact: string | null;
  is_anonymous: boolean;
  bureau_id: string | null;
  bureau: { id: string; code: string; name: string } | null;
  priority: Priority;
  status: ComplaintStatus;
  created_at: string;
  updated_at: string;
}

export interface CaseAction {
  id: string;
  case_id: string;
  action_type: string;
  description: string;
  performed_by: User;
  performed_at: string;
  remarks: string | null;
  previous_status: CaseStatus | null;
  new_status: CaseStatus | null;
  metadata: Record<string, unknown> | null;
}

export interface CaseAssignment {
  id: string;
  case_id: string;
  assigned_to: User;
  assigned_by: User;
  assigned_at: string;
  unassigned_at: string | null;
  remarks: string | null;
}

export interface Document {
  id: string;
  case_id: string | null;
  complaint_id: string | null;
  filename: string;
  content_type: string;
  file_size: number;
  storage_key: string;
  uploaded_by: User;
  uploaded_at: string;
  is_confidential: boolean;
}

export interface OverlapReview {
  id: string;
  overlap_alert_id: string;
  reviewed_by: User;
  reviewed_at: string;
  decision: OverlapStatus;
  remarks: string;
  linked_case_ids: string[];
}

// Matches actual API response from /api/v1/overlaps
export interface OverlapAlert {
  id: string;
  alert_number: string;
  case_id_incoming: string;
  case_id_existing: string;
  institution_id: string | null;
  match_type: string;
  match_score: number;          // 0–100
  match_evidence: Record<string, unknown> | null;
  bureaus_involved: string[];   // array of bureau UUIDs
  status: OverlapStatus;
  created_at: string;
  updated_at: string;
  // Explainability fields
  match_reasons: string[] | null;
  detection_method: string | null;
  similarity_score: number | null;
  // Optional fields that may be present in detail view
  review?: {
    decision: string;
    remarks: string | null;
    reviewed_by: { full_name: string };
    reviewed_at: string;
  } | null;
}

export interface RelatedCase {
  id: string;
  primary_case_id: string;
  related_case_id: string;
  relationship_type: string;
  rationale: string | null;
  linked_by: User;
  linked_at: string;
  coordination_notes: string | null;
}

// Matches actual /api/v1/cases response
export interface Case {
  id: string;
  case_number: string;
  complaint_id: string | null;
  institution_id: string | null;
  bureau_id: string | null;
  category_id: string | null;
  subject: string;
  description: string;
  status: CaseStatus;
  priority: Priority;
  sla_days: number | null;
  expected_disposal_date: string | null;  // replaces sla_deadline
  disposal_date: string | null;
  disposal_remarks: string | null;
  created_at: string;
  updated_at: string;
  created_by_id: string | null;
  // Nested objects returned by API
  assigned_officer: { id: string; email: string; full_name: string } | null;
  bureau: { id: string; code: string; name: string } | null;
  category: { id: string; code: string; name: string } | null;
  // Only in detail endpoint
  recent_actions?: CaseAction[];
  current_assignment?: CaseAssignment | null;
}

// Matches actual /api/v1/notifications response
export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  is_read: boolean;
  created_at: string;
}

// Matches actual /api/v1/audit-logs response
export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string;
  actor_email: string;
  timestamp: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  remarks: string | null;
  request_id: string | null;
  ip_address: string | null;
}

export interface SLARule {
  id: string;
  name: string;
  bureau: Bureau | null;
  category: string | null;
  priority: Priority | null;
  days_to_resolve: number;
  warning_days_before: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Institution Digital Twin ─────────────────────────────────────────────────

export interface BureauCaseSummary {
  bureau_id: string;
  bureau_name: string;
  bureau_code: string;
  total_cases: number;
  active_cases: number;
  disposed_cases: number;
}

export interface CaseHistoryEntry {
  id: string;
  case_number: string;
  subject: string;
  status: string;
  priority: string;
  bureau_name: string | null;
  expected_disposal_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssignedOfficerEntry {
  officer_id: string;
  officer_name: string;
  officer_email: string;
  bureau_name: string | null;
  case_ids: string[];
}

export interface InstitutionProfile {
  institution: Institution;
  total_complaints: number;
  total_cases: number;
  active_cases: number;
  pending_cases: number;
  under_process_cases: number;
  disposed_cases: number;
  transferred_cases: number;
  escalated_cases: number;
  overdue_cases: number;
  unresolved_overlap_alerts: number;
  bureau_breakdown: BureauCaseSummary[];
  assigned_officers: AssignedOfficerEntry[];
  case_history: CaseHistoryEntry[];
  latest_activity: string | null;
}

export interface GraphNode {
  id: string;
  node_type: "institution" | "case" | "complaint" | "bureau";
  label: string;
  status: string | null;
  url: string | null;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string | null;
}

export interface InstitutionGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ─── Conflict Alerts ──────────────────────────────────────────────────────────

export type ConflictSeverity = "low" | "medium" | "high";
export type ConflictStatus = "open" | "acknowledged" | "resolved" | "dismissed";

export interface ConflictAlert {
  id: string;
  institution_id: string | null;
  institution_name: string | null;
  case_ids: string[] | null;
  bureau_ids: string[] | null;
  rule_triggered: string;
  rule_description: string | null;
  evidence: Record<string, unknown> | null;
  severity: ConflictSeverity;
  recommended_action: string | null;
  coordination_owner_id: string | null;
  coordination_owner_name: string | null;
  status: ConflictStatus;
  resolution_note: string | null;
  resolved_by_id: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConflictReviewRequest {
  action: "acknowledge" | "assign" | "resolve" | "dismiss";
  resolution_note?: string;
  coordination_owner_id?: string;
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;   // API returns page_size, not size
  size?: number;       // kept for backwards-compat
  pages: number;
}

export interface PaginationParams {
  page?: number;
  size?: number;
}

// ─── Dashboard / Analytics ────────────────────────────────────────────────────

// Matches actual API response from /api/v1/dashboard/summary
export interface DashboardSummary {
  total_complaints: number;
  total_cases: number;
  active_cases: number;
  pending_assignment: number;
  under_process: number;
  awaiting_information: number;
  transferred: number;
  escalated: number;
  disposed: number;
  closed: number;
  overdue_cases: number;
  cases_approaching_deadline: number;
  overlaps_pending_review: number;
  overlaps_confirmed: number;
  overlaps_false_positive: number;
  conflict_warnings_unresolved: number;
}

// Matches actual API response from /api/v1/dashboard/trends
export interface TrendData {
  period: string;      // "2026-10"
  intake: number;
  disposed: number;
  active: number;
}

// Matches actual API response from /api/v1/dashboard/workload
export interface WorkloadData {
  entity_id: string;
  entity_name: string;
  entity_type: string;  // "bureau" | "officer"
  total_cases: number;
  active_cases: number;
  overdue_cases: number;
}

export interface AgeingBucket {
  bucket: string; // e.g. "0-30 days", "31-60 days"
  count: number;
}

// ─── Filter / Search params ───────────────────────────────────────────────────

export interface CaseFilterParams extends PaginationParams {
  institution_id?: string;
  bureau_id?: string;
  region_id?: string;
  status?: CaseStatus;
  priority?: Priority;
  category?: string;
  assigned_officer_id?: string;
  is_overdue?: boolean;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface ComplaintFilterParams extends PaginationParams {
  institution_id?: string;
  bureau_id?: string;
  status?: ComplaintStatus;
  priority?: Priority;
  category?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface OverlapFilterParams extends PaginationParams {
  status?: OverlapStatus;
  match_type?: MatchType;
  bureau_id?: string;
  date_from?: string;
  date_to?: string;
}
