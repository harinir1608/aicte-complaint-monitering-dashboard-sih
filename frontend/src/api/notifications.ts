import apiClient from "@/lib/api";
import type { Notification, PaginatedResponse } from "@/types";

export async function getNotifications(
  page = 1,
  size = 20
): Promise<PaginatedResponse<Notification>> {
  const response = await apiClient.get<PaginatedResponse<Notification>>(
    "/notifications",
    { params: { page, size } }
  );
  return response.data;
}

export async function markAsRead(id: string): Promise<void> {
  await apiClient.post(`/notifications/${id}/read`);
}

export async function markAllAsRead(): Promise<void> {
  await apiClient.post("/notifications/read-all");
}

export async function getUnreadCount(): Promise<number> {
  const response = await apiClient.get<{ count: number }>(
    "/notifications/unread-count"
  );
  return response.data.count;
}
