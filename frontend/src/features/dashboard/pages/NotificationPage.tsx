import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Bell, Check } from "lucide-react";

// Helper for relative time
function formatTimeAgo(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return "Just now";
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays}d ago`;
}

import { notificationService } from "../../../services/notificationService";
import { Button } from "../../../components/ui/Button";
import { Card, CardContent } from "../../../components/ui/Card";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";
import { Badge } from "../../../components/ui/Badge";

export default function NotificationPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filterUnread, setFilterUnread] = useState(false);
  const pageSize = 15;

  const { data, isLoading } = useQuery({
    queryKey: ["allNotifications", page, pageSize, filterUnread],
    queryFn: () => notificationService.listNotifications({ page, page_size: pageSize, unread_only: filterUnread }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
      queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
      queryClient.invalidateQueries({ queryKey: ["unreadNotificationCount"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
      queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
      queryClient.setQueryData(["unreadNotificationCount"], 0);
    },
  });

  const notifications = data?.data || [];
  const pagination = data?.pagination;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-text flex items-center gap-2">
          <Bell className="h-6 w-6 text-primary" />
          Notifications
        </h1>
        
        <div className="flex items-center gap-3">
          <div className="bg-bg-secondary p-1 rounded-lg inline-flex">
            <button
              onClick={() => { setFilterUnread(false); setPage(1); }}
              className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                !filterUnread ? "bg-bg text-text shadow-sm" : "text-text-secondary hover:text-text"
              }`}
            >
              All
            </button>
            <button
              onClick={() => { setFilterUnread(true); setPage(1); }}
              className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                filterUnread ? "bg-bg text-text shadow-sm" : "text-text-secondary hover:text-text"
              }`}
            >
              Unread
            </button>
          </div>
          
          <Button 
            variant="outline" 
            size="sm" 
            className="text-xs h-8"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
          >
            <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
            Mark all read
          </Button>
        </div>
      </div>

      <Card className="bg-card border-border shadow-xs">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-20">
              <LoadingSpinner size="lg" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-20">
              <Bell className="h-12 w-12 text-text-tertiary mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-bold text-text">No notifications found</h3>
              <p className="text-text-secondary mt-1 text-sm">
                {filterUnread ? "You have read all your notifications." : "You have no notifications yet."}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {notifications.map((notification) => (
                <div 
                  key={notification.id} 
                  className={`p-5 flex flex-col sm:flex-row sm:items-start gap-4 transition-colors ${
                    !notification.is_read ? "bg-primary/5 hover:bg-primary/10" : "bg-bg hover:bg-bg-secondary/50"
                  }`}
                >
                  <div className="flex-1 space-y-1.5">
                    <div className="flex items-center gap-2">
                      {!notification.is_read && (
                        <span className="h-2 w-2 rounded-full bg-primary shrink-0" />
                      )}
                      <h4 className={`text-sm ${!notification.is_read ? "font-bold text-text" : "font-medium text-text-secondary"}`}>
                        {notification.title}
                      </h4>
                      <Badge variant="outline" className="text-[10px] uppercase py-0 leading-tight tracking-wider ml-2">
                        {notification.type.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className={`text-sm leading-relaxed ${!notification.is_read ? "text-text" : "text-text-secondary"}`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-text-tertiary font-medium">
                      {formatTimeAgo(notification.created_at)}
                    </p>
                  </div>
                  
                  {!notification.is_read && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="shrink-0 text-xs h-8 cursor-pointer"
                      onClick={() => markReadMutation.mutate(notification.id)}
                      disabled={markReadMutation.isPending}
                    >
                      <Check className="h-3.5 w-3.5 mr-1.5" />
                      Mark read
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-between items-center pb-8">
          <Button
            variant="outline"
            disabled={!pagination.has_prev}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-text-secondary font-medium">
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <Button
            variant="outline"
            disabled={!pagination.has_next}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
