import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Bell, Check } from "lucide-react";
import styles from "./NotificationPage.module.css";

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
import { apiClient } from "../../../lib/axios";
import { LoadingSpinner } from "../../../components/common/LoadingSpinner";

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
    <div className={styles.pageContainer}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Bell style={{ height: "1.5rem", width: "1.5rem", color: "var(--color-primary)" }} />
          Notifications
        </h1>
        
        <div className={styles.actions}>
          <div className={styles.filterGroup}>
            <button
              onClick={() => { setFilterUnread(false); setPage(1); }}
              className={`${styles.filterBtn} ${!filterUnread ? styles.filterBtnActive : ""}`}
            >
              All
            </button>
            <button
              onClick={() => { setFilterUnread(true); setPage(1); }}
              className={`${styles.filterBtn} ${filterUnread ? styles.filterBtnActive : ""}`}
            >
              Unread
            </button>
          </div>
          
          <button 
            className={styles.actionBtn}
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending || notifications.length === 0}
          >
            <CheckCircle2 style={{ height: "0.875rem", width: "0.875rem", marginRight: "0.375rem" }} />
            Mark all read
          </button>
          
          <button 
            className={`${styles.actionBtn} ${styles.actionBtnDanger}`}
            onClick={async () => {
              await apiClient.delete("/notifications/clear-all");
              queryClient.invalidateQueries({ queryKey: ["allNotifications"] });
              queryClient.invalidateQueries({ queryKey: ["latestNotifications"] });
              queryClient.setQueryData(["unreadNotificationCount"], 0);
            }}
            disabled={notifications.length === 0}
          >
            Clear all
          </button>
        </div>
      </div>

      <div className={styles.card}>
        {isLoading ? (
          <div className={styles.loading}>
            <LoadingSpinner size="lg" />
          </div>
        ) : notifications.length === 0 ? (
          <div className={styles.empty}>
            <Bell style={{ height: "2.5rem", width: "2.5rem", color: "var(--color-primary)", marginBottom: "1rem" }} />
            <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "var(--color-text)", marginBottom: "0.5rem" }}>No notifications found</h3>
            <p>{filterUnread ? "You have read all your notifications." : "You have no notifications yet."}</p>
          </div>
        ) : (
          <div className={styles.list}>
            {notifications.map((notification) => (
              <div 
                key={notification.id} 
                className={`${styles.item} ${!notification.is_read ? styles.unread : styles.read}`}
              >
                <div className={styles.itemContent}>
                  <div className={styles.itemHeader}>
                    {!notification.is_read && (
                      <div className={styles.dot} />
                    )}
                    <h4 className={styles.itemTitle}>
                      {notification.title}
                    </h4>
                    <span className={styles.badge}>
                      {notification.type.replace("_", " ")}
                    </span>
                  </div>
                  <p className={styles.itemMessage}>
                    {notification.message}
                  </p>
                  <p className={styles.itemTime}>
                    {formatTimeAgo(notification.created_at)}
                  </p>
                </div>
                
                {!notification.is_read && (
                  <button
                    className={styles.markReadBtn}
                    onClick={() => markReadMutation.mutate(notification.id)}
                    disabled={markReadMutation.isPending}
                  >
                    <Check style={{ height: "0.875rem", width: "0.875rem", marginRight: "0.375rem" }} />
                    Mark read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {pagination && pagination.total_pages > 1 && (
        <div className={styles.pagination}>
          <button
            className={styles.actionBtn}
            disabled={!pagination.has_prev}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <span className={styles.pageInfo}>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          <button
            className={styles.actionBtn}
            disabled={!pagination.has_next}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
