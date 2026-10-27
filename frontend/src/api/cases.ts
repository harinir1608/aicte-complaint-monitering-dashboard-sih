import apiClient from "@/lib/api";
import type {
  Case,
  CaseAction,
  PaginatedResponse,
  CaseFilterParams,
  CaseStatus,
  RelatedCase,
} from "@/types";

export async function getCases(
  filters: CaseFilterParams = {}
): Promise<PaginatedResponse<Case>> {
  const response = await apiClient.get<PaginatedResponse<Case>>("/cases", {
    params: filters,
  });
  return response.data;
}

export async function getCase(id: string): Promise<Case> {
  const response = await apiClient.get<Case>(`/cases/${id}`);
  return response.data;
}

export async function updateCaseStatus(
  id: string,
  status: CaseStatus,
  remarks?: string
): Promise<Case> {
  const response = await apiClient.patch<Case>(`/cases/${id}/status`, {
    new_status: status,
    remarks,
  });
  return response.data;
}

export async function assignCase(
  id: string,
  officerId: string,
  notes?: string
): Promise<Case> {
  const response = await apiClient.post<Case>(`/cases/${id}/assign`, {
    officer_id: officerId,
    notes,
  });
  return response.data;
}

export async function transferCase(
  id: string,
  bureauId: string,
  reason: string
): Promise<Case> {
  const response = await apiClient.post<Case>(`/cases/${id}/transfer`, {
    bureau_id: bureauId,
    reason,
  });
  return response.data;
}

export async function addCaseAction(
  id: string,
  action: {
    action_type: string;
    description: string;
    remarks?: string;
    new_status?: CaseStatus;
  }
): Promise<CaseAction> {
  const response = await apiClient.post<CaseAction>(
    `/cases/${id}/actions`,
    action
  );
  return response.data;
}

export async function getCaseHistory(id: string): Promise<CaseAction[]> {
  const response = await apiClient.get<CaseAction[]>(`/cases/${id}/history`);
  return response.data;
}

export async function linkCases(
  id: string,
  relatedId: string,
  relationship: string,
  rationale: string
): Promise<RelatedCase> {
  const response = await apiClient.post<RelatedCase>(
    `/cases/${id}/related-cases`,
    { related_case_id: relatedId, relationship_type: relationship, rationale }
  );
  return response.data;
}

export async function getRelatedCases(id: string): Promise<RelatedCase[]> {
  const response = await apiClient.get<RelatedCase[]>(
    `/cases/${id}/related-cases`
  );
  return response.data;
}

export async function uploadCaseDocument(
  id: string,
  file: File,
  isConfidential = false
): Promise<{ id: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("is_confidential", String(isConfidential));

  const response = await apiClient.post<{ id: string; filename: string }>(
    `/cases/${id}/documents`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}
