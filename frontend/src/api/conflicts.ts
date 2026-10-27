import apiClient from "@/lib/api";
import type { ConflictAlert, ConflictReviewRequest, PaginatedResponse } from "@/types";

export interface ConflictFilterParams {
  institution_id?: string;
  severity?: string;
  status?: string;
  bureau_id?: string;
  page?: number;
  page_size?: number;
}

export async function getConflicts(
  filters: ConflictFilterParams = {}
): Promise<PaginatedResponse<ConflictAlert>> {
  const response = await apiClient.get<PaginatedResponse<ConflictAlert>>("/conflicts", {
    params: filters,
  });
  return response.data;
}

export async function getConflict(id: string): Promise<ConflictAlert> {
  const response = await apiClient.get<ConflictAlert>(`/conflicts/${id}`);
  return response.data;
}

export async function reviewConflict(
  id: string,
  data: ConflictReviewRequest
): Promise<ConflictAlert> {
  const response = await apiClient.post<ConflictAlert>(`/conflicts/${id}/review`, data);
  return response.data;
}

export async function triggerConflictScan(): Promise<{ alerts_created: number; message: string }> {
  const response = await apiClient.post<{ alerts_created: number; message: string }>(
    "/conflicts/scan"
  );
  return response.data;
}
