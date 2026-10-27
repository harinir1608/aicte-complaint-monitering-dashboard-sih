/**
 * useNotifications — polls the backend for unread notification count every 60 s.
 *
 * Usage:
 *   const { unreadCount, notifications, refresh } = useNotifications();
 */
import { useCallback, useEffect, useRef, useState } from "react";
import apiClient from "@/lib/api";

interface Notification {
  id: string;
  title: string;
  message: string | null;
  notification_type: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  is_read: boolean;
  created_at: string;
}

interface NotificationsState {
  unreadCount: number;
  notifications: Notification[];
  isLoading: boolean;
  refresh: () => void;
}

const POLL_INTERVAL_MS = 60_000; // 60 seconds

export function useNotifications(): NotificationsState {
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch unread count
      const countResp = await apiClient.get<{ unread_count: number }>(
        "/notifications/count"
      );
      setUnreadCount(countResp.data.unread_count);

      // Fetch notifications list (first page)
      const listResp = await apiClient.get<{
        items: Notification[];
        total: number;
      }>("/notifications?page=1&page_size=20");
      setNotifications(listResp.data.items);
    } catch {
      // Silently fail — avoid noise when unauthenticated or network issues
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchNotifications();

    // Poll every 60 seconds
    intervalRef.current = setInterval(fetchNotifications, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchNotifications]);

  return {
    unreadCount,
    notifications,
    isLoading,
    refresh: fetchNotifications,
  };
}
