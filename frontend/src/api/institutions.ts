import apiClient from "@/lib/api";
import type { Institution, InstitutionProfile, InstitutionGraph, PaginatedResponse, Case } from "@/types";

export interface InstitutionFilters {
  name?: string;            // backend param — searches name + permanent_id
  search?: string;          // alias mapped to name before sending
  state?: string;
  region_id?: string;
  institution_type?: string;
  is_active?: boolean;
  page?: number;
  size?: number;
}

export interface InstitutionCreateData {
  name: string;
  aicte_permanent_id?: string;
  address?: string;
  city?: string;
  district?: string;
  state?: string;
  region_id?: string;
  institution_type?: string;
  phone?: string;
  email?: string;
  website?: string;
}

export async function getInstitutions(
  filters: InstitutionFilters = {}
): Promise<PaginatedResponse<Institution>> {
  // Map `search` → `name` (the actual backend param)
  const { search, ...rest } = filters;
  const params = { ...rest, ...(search ? { name: search } : {}) };
  const response = await apiClient.get<PaginatedResponse<Institution>>(
    "/institutions",
    { params }
  );
  return response.data;
}

export async function getInstitution(id: string): Promise<Institution> {
  const response = await apiClient.get<Institution>(`/institutions/${id}`);
  return response.data;
}

export async function createInstitution(
  data: InstitutionCreateData
): Promise<Institution> {
  const response = await apiClient.post<Institution>("/institutions", data);
  return response.data;
}

export async function updateInstitution(
  id: string,
  data: Partial<InstitutionCreateData>
): Promise<Institution> {
  const response = await apiClient.patch<Institution>(
    `/institutions/${id}`,
    data
  );
  return response.data;
}

export async function getInstitutionCases(
  id: string,
  filters: { page?: number; size?: number; status?: string } = {}
): Promise<PaginatedResponse<Case>> {
  const response = await apiClient.get<PaginatedResponse<Case>>(
    `/institutions/${id}/cases`,
    { params: filters }
  );
  return response.data;
}

export async function searchInstitutions(
  query: string,
  limit = 10
): Promise<Institution[]> {
  const response = await apiClient.get<Institution[]>("/institutions/search", {
    params: { q: query, limit },
  });
  return response.data;
}

export async function getInstitutionProfile(id: string): Promise<InstitutionProfile> {
  const response = await apiClient.get<InstitutionProfile>(`/institutions/${id}/profile`);
  return response.data;
}

export async function getInstitutionGraph(id: string): Promise<InstitutionGraph> {
  const response = await apiClient.get<InstitutionGraph>(`/institutions/${id}/graph`);
  return response.data;
}

export async function addInstitutionAlias(
  id: string,
  alias: string,
  aliasType = "other"
): Promise<Institution> {
  const response = await apiClient.post<Institution>(
    `/institutions/${id}/aliases`,
    { alias, alias_type: aliasType }
  );
  return response.data;
}
