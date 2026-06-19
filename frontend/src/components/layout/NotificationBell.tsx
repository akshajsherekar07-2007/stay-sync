import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Bell, Check, CheckCircle2 } from "lucide-react";
import { useWebSocket } from "../../hooks/useWebSocket";
import { notificationService } from "../../services/notificationService";
import { apiClient } from "../../lib/axios";
import { useAuthStore } from "../../stores/authStore";
import { Button } from "../ui/Button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
} from "../ui/DropdownMenu";
import styles from "./NotificationBell.module.css";

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

export function NotificationBell() {
  const { isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const { isConnected } = useWebSocket();

  // Poll for unread count — longer interval when WebSocket is active
  const { data: unreadCount = 0 } = useQuery({
    queryKey: ["unreadNotificationCount"],
    queryFn: () => notificationService.getUnreadCount(),
    enabled: isAuthenticated,
    refetchInterval: isConnected ? 120_000 : 30_000, // 2min with WS, 30s without
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
        <Button variant="ghost" size="icon" style={{ position: "relative", borderRadius: "50%", cursor: "pointer" }}>
          <Bell style={{ height: "1.25rem", width: "1.25rem", color: "var(--color-text-secondary)" }} />
          {unreadCount > 0 && (
            <span style={{
              position: "absolute", top: "0.375rem", right: "0.25rem", display: "flex", alignItems: "center", justifyContent: "center",
              height: "1rem", width: "1rem", borderRadius: "50%", backgroundColor: "var(--color-danger)",
              color: "#fff", fontSize: "0.5625rem", fontWeight: "bold", border: "2px solid var(--color-bg)"
            }}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className={styles.dropdownContent} style={{ padding: 0 }}>
        <div className={styles.header}>
          <h3 className={styles.headerTitle}>Notifications</h3>
          <div className={styles.headerActions}>
            {unreadCount > 0 && (
              <button 
                className={`${styles.actionButton} ${styles.actionButtonPrimary}`}
                onClick={(e) => {
                  e.preventDefault();
                  markAllReadMutation.mutate();
                }}
                disabled={markAllReadMutation.isPending}
              >
                <CheckCircle2 style={{ height: "0.75rem", width: "0.75rem", marginRight: "0.25rem" }} />
                Mark all read
              </button>
            )}
            {notifications.length > 0 && (
              <button 
                className={`${styles.actionButton} ${styles.actionButtonDanger}`}
                onClick={async (e) => {
                  e.preventDefault();
                  await apiClient.delete("/notifications/clear-all");
                  queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
                  queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
                  queryClient.setQueryData(["unreadNotificationCount"], 0);
                }}
              >
                Clear all
              </button>
            )}
          </div>
        </div>
        
        <div className={styles.notificationList}>
          {isLoading ? (
            <div className={styles.emptyState}>Loading notifications...</div>
          ) : notifications.length === 0 ? (
            <div className={styles.emptyState}>
              <Bell style={{ height: "2rem", width: "2rem", marginBottom: "0.5rem", opacity: 0.5 }} />
              <p>You have no notifications</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <div 
                key={notification.id} 
                className={`${styles.notificationItem} ${!notification.is_read ? styles.unread : styles.read}`}
              >
                <div className={styles.itemContent}>
                  <p className={styles.itemTitle}>{notification.title}</p>
                  <p className={styles.itemMessage}>{notification.message}</p>
                  <p className={styles.itemTime}>{formatTimeAgo(notification.created_at)}</p>
                </div>
                {!notification.is_read && (
                  <button 
                    className={styles.markReadBtn}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      markReadMutation.mutate(notification.id);
                    }}
                    title="Mark as read"
                  >
                    <Check style={{ height: "0.75rem", width: "0.75rem" }} />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
        
        <div className={styles.footer}>
          <Link to="/notifications" className={styles.viewAll} onClick={() => setIsOpen(false)}>
            View all notifications
          </Link>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
