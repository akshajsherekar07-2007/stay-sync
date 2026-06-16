import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Bell, Check, CheckCircle2 } from "lucide-react";

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

import { notificationService } from "../../services/notificationService";
import { useAuthStore } from "../../stores/authStore";
import { Button } from "../ui/Button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
} from "../ui/DropdownMenu";

export function NotificationBell() {
  const { isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);

  // Poll for unread count
  const { data: unreadCount = 0 } = useQuery({
    queryKey: ["unreadNotificationCount"],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: isAuthenticated,
    refetchInterval: 30000, // Poll every 30 seconds
  });

  // Fetch latest notifications when dropdown is open
  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ["latestNotifications"],
    queryFn: () => notificationService.listNotifications({ page_size: 5 }),
    enabled: isOpen && isAuthenticated,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationService.markAsRead(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["latestNotifications"] });
      const previousData = queryClient.getQueryData(["latestNotifications"]);
      
      // Optimistically update the unread count and the specific notification
      queryClient.setQueryData(["unreadNotificationCount"], (old: number) => Math.max(0, (old || 1) - 1));
      
      queryClient.setQueryData(["latestNotifications"], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          data: old.data.map((n: any) => n.id === id ? { ...n, is_read: true } : n)
        };
      });
      return { previousData };
    },
    onError: (_err, _newVal, context) => {
      queryClient.setQueryData(["latestNotifications"], context?.previousData);
      queryClient.invalidateQueries({ queryKey: ["unreadNotificationCount"] });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["unreadNotificationCount"] });
      queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
      queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onSuccess: () => {
      queryClient.setQueryData(["unreadNotificationCount"], 0);
      queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
      queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
    },
  });

  if (!isAuthenticated) return null;

  const notifications = notificationsData?.data || [];

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative h-10 w-10 rounded-full cursor-pointer">
          <Bell className="h-5 w-5 text-text-secondary" />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[9px] font-bold text-white shadow-sm ring-2 ring-bg">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-80 sm:w-96 p-0 border-border bg-bg shadow-lg">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
          <h3 className="font-semibold text-text text-sm">Notifications</h3>
          {unreadCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-xs text-primary hover:text-primary-dark h-auto py-1 px-2 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                markAllReadMutation.mutate();
              }}
              disabled={markAllReadMutation.isPending}
            >
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
        </div>
        
        <div className="max-h-[300px] overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-xs text-text-tertiary">Loading notifications...</div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center flex flex-col items-center">
              <Bell className="h-8 w-8 text-text-tertiary mb-2 opacity-50" />
              <p className="text-sm text-text-secondary">You have no notifications</p>
            </div>
          ) : (
            <div className="flex flex-col">
              {notifications.map((notification) => (
                <div 
                  key={notification.id} 
                  className={`flex items-start gap-3 p-3 border-b border-border/30 transition-colors ${
                    !notification.is_read ? "bg-primary/5 hover:bg-primary/10" : "bg-bg hover:bg-bg-secondary"
                  }`}
                >
                  <div className="flex-1 min-w-0 space-y-1">
                    <p className={`text-sm ${!notification.is_read ? "font-semibold text-text" : "font-medium text-text-secondary"}`}>
                      {notification.title}
                    </p>
                    <p className={`text-xs line-clamp-2 ${!notification.is_read ? "text-text-secondary" : "text-text-tertiary"}`}>
                      {notification.message}
                    </p>
                    <p className="text-[10px] text-text-tertiary font-medium">
                      {formatTimeAgo(notification.created_at)}
                    </p>
                  </div>
                  {!notification.is_read && (
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6 shrink-0 rounded-full hover:bg-primary/20 hover:text-primary cursor-pointer text-text-tertiary"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        markReadMutation.mutate(notification.id);
                      }}
                      title="Mark as read"
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="p-2 border-t border-border/50">
          <Button asChild variant="ghost" className="w-full text-xs h-8 text-text-secondary hover:text-text cursor-pointer">
            <Link to="/notifications" onClick={() => setIsOpen(false)}>
              View all notifications
            </Link>
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
