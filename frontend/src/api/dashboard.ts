import apiClient from "@/lib/api";
import type {
  DashboardSummary,
  TrendData,
  WorkloadData,
  Institution,
  PaginatedResponse,
} from "@/types";

export interface DashboardFilters {
  date_from?: string;
  date_to?: string;
  region_id?: string;
  bureau_id?: string;
  category?: string;
  status?: string;
  priority?: string;
}

export async function getDashboardSummary(
  filters: DashboardFilters = {}
): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>(
    "/dashboard/summary",
    { params: filters }
  );
  return response.data;
}

export async function getDashboardTrends(
  filters: DashboardFilters = {}
): Promise<TrendData[]> {
  const response = await apiClient.get<TrendData[]>("/dashboard/trends", {
    params: filters,
  });
  return response.data;
}

export async function getDashboardWorkload(
  filters: DashboardFilters = {}
): Promise<WorkloadData[]> {
  const response = await apiClient.get<WorkloadData[]>(
    "/dashboard/workload",
    { params: filters }
  );
  return response.data;
}

export async function getInstitutionTable(
  filters: DashboardFilters & { page?: number; size?: number; search?: string } = {}
): Promise<PaginatedResponse<Institution>> {
  const response = await apiClient.get<PaginatedResponse<Institution>>(
    "/dashboard/institutions",
    { params: filters }
  );
  return response.data;
}
