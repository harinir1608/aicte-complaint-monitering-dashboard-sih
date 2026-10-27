import apiClient from "@/lib/api";
import type {
  OverlapAlert,
  PaginatedResponse,
  OverlapFilterParams,
  OverlapStatus,
} from "@/types";

export async function getOverlaps(
  filters: OverlapFilterParams = {}
): Promise<PaginatedResponse<OverlapAlert>> {
  const response = await apiClient.get<PaginatedResponse<OverlapAlert>>(
    "/overlaps",
    { params: filters }
  );
  return response.data;
}

export async function getOverlap(id: string): Promise<OverlapAlert> {
  const response = await apiClient.get<OverlapAlert>(`/overlaps/${id}`);
  return response.data;
}

export async function reviewOverlap(
  id: string,
  decision: OverlapStatus,
  remarks: string,
  linkedCaseIds?: string[]
): Promise<OverlapAlert> {
  const response = await apiClient.post<OverlapAlert>(
    `/overlaps/${id}/review`,
    { decision, remarks, linked_case_ids: linkedCaseIds ?? [] }
  );
  return response.data;
}

export async function runOverlapCheck(caseId: string): Promise<{ alerts_created: number }> {
  const response = await apiClient.post<{ alerts_created: number }>(
    `/cases/${caseId}/check-overlaps`
  );
  return response.data;
}
