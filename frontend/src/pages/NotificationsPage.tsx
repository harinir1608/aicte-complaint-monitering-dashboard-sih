import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getNotifications, markAsRead, markAllAsRead } from "@/api/notifications";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Bell, CheckCheck, ExternalLink } from "lucide-react";
import { timeAgo } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", page],
    queryFn: () => getNotifications(page),
  });

  const markReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast({ title: "All notifications marked as read" });
    },
  });

  const unreadCount = data?.items.filter((n) => !n.is_read).length ?? 0;

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle="In-app alerts, reminders, and case updates"
        breadcrumbs={[{ label: "Home", href: "/" }, { label: "Notifications" }]}
        actions={
          unreadCount > 0 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => markAllMutation.mutate()}
              isLoading={markAllMutation.isPending}
            >
              <CheckCheck className="mr-2 h-4 w-4" />
              Mark All as Read
            </Button>
          ) : null
        }
      />

      <div className="p-6 space-y-3 max-w-3xl">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))
        ) : data?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Bell className="h-12 w-12 mb-3" />
            <p className="text-sm">No notifications yet.</p>
          </div>
        ) : (
          data?.items.map((notification) => (
            <Card
              key={notification.id}
              className={cn(
                "transition-colors cursor-pointer hover:bg-gray-50",
                !notification.is_read && "border-l-4 border-l-indigo-500 bg-indigo-50/30"
              )}
              onClick={() => {
                if (!notification.is_read) markReadMutation.mutate(notification.id);
                if (notification.related_entity_type === "case" && notification.related_entity_id)
                  window.location.href = `/cases/${notification.related_entity_id}`;
                else if (notification.related_entity_type === "overlap_alert" && notification.related_entity_id)
                  window.location.href = `/overlaps/${notification.related_entity_id}`;
              }}
            >
              <CardContent className="flex items-start gap-3 p-4">
                <div className={cn(
                  "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                  !notification.is_read ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-400"
                )}>
                  <Bell className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className={cn("text-sm font-medium", !notification.is_read ? "text-gray-900" : "text-gray-700")}>
                      {notification.title}
                    </p>
                    <div className="flex items-center gap-2 shrink-0">
                      {!notification.is_read && (
                        <Badge variant="default" className="text-xs px-1.5 py-0">New</Badge>
                      )}
                      <span className="text-xs text-gray-400">{timeAgo(notification.created_at)}</span>
                    </div>
                  </div>
                  <p className="mt-0.5 text-sm text-gray-500">{notification.message}</p>
                  {notification.related_entity_id && (
                    <span className="mt-1 inline-flex items-center gap-1 text-xs text-indigo-600">
                      View details <ExternalLink className="h-3 w-3" />
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}

        {data && data.pages > 1 && (
          <div className="flex justify-center gap-3 pt-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
            <span className="text-sm text-gray-500 self-center">Page {page} of {data.pages}</span>
            <Button variant="outline" size="sm" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)}>Next</Button>
          </div>
        )}
      </div>
    </div>
  );
}
