import apiClient from "@/lib/api";
import type {
  Complaint,
  Case,
  PaginatedResponse,
  ComplaintFilterParams,
} from "@/types";

export interface ComplaintCreateData {
  institution_id: string;
  received_date: string;
  source: string;
  category: string;
  subject: string;
  description: string;
  bureau_id: string;
  priority: string;
  assigned_officer_id?: string;
  sla_deadline?: string;
}

export async function getComplaints(
  filters: ComplaintFilterParams = {}
): Promise<PaginatedResponse<Complaint>> {
  const response = await apiClient.get<PaginatedResponse<Complaint>>(
    "/complaints",
    { params: filters }
  );
  return response.data;
}

export async function getComplaint(id: string): Promise<Complaint> {
  const response = await apiClient.get<Complaint>(`/complaints/${id}`);
  return response.data;
}

export async function createComplaint(
  data: ComplaintCreateData
): Promise<Complaint> {
  const response = await apiClient.post<Complaint>("/complaints", data);
  return response.data;
}

export async function updateComplaint(
  id: string,
  data: Partial<ComplaintCreateData>
): Promise<Complaint> {
  const response = await apiClient.patch<Complaint>(`/complaints/${id}`, data);
  return response.data;
}

export async function uploadComplaintDocument(
  id: string,
  file: File,
  isConfidential = false
): Promise<{ id: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("is_confidential", String(isConfidential));

  const response = await apiClient.post<{ id: string; filename: string }>(
    `/complaints/${id}/documents`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export async function createCaseFromComplaint(
  id: string,
  bureauId: string
): Promise<Case> {
  const response = await apiClient.post<Case>(
    `/complaints/${id}/create-case`,
    { bureau_id: bureauId }
  );
  return response.data;
}
