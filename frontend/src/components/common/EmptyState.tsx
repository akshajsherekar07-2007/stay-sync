import * as React from "react";
import { cn } from "../../lib/utils";
import styles from "./EmptyState.module.css";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ComponentType<{ className?: string }> | React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({
  className,
  icon: Icon,
  title,
  description,
  action,
  ...props
}: EmptyStateProps) {
  const isIconComponent = typeof Icon === "function" || (Icon && typeof (Icon as any).render === "function");
  return (
    <div
      className={cn(styles.container, className)}
      {...props}
    >
      <div className={styles.backgroundBlob} />
      <div className={styles.iconContainer}>
        {Icon ? (
          isIconComponent ? (
            // @ts-ignore
            <Icon className={styles.icon} />
          ) : (
            Icon
          )
        ) : (
          <svg
            className={styles.icon}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.008 1.24l.885 1.77a2.25 2.25 0 0 0 2.007 1.24h1.98a2.25 2.25 0 0 0 2.007-1.24l.885-1.77a2.25 2.25 0 0 1 2.007-1.24h3.86m-18 0h18a2.25 2.25 0 0 1 2.25 2.25v4.5A2.25 2.25 0 0 1 18.75 21H5.25A2.25 2.25 0 0 1 3 18.75v-4.5A2.25 2.25 0 0 1 5.25 13.5z"
            />
          </svg>
        )}
      </div>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
