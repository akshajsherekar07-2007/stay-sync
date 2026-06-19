import * as React from "react";
import { cn } from "../../lib/utils";

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
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center rounded-[24px] bg-card border-none shadow-sm p-8 text-center animate-fade-in relative overflow-hidden",
        className
      )}
      {...props}
    >
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-inner relative z-10 mb-6">
        {Icon ? (
          isIconComponent ? (
            // @ts-ignore
            <Icon className="h-10 w-10 text-primary" />
          ) : (
            Icon
          )
        ) : (
          <svg
            className="h-10 w-10 text-primary"
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
      <h3 className="text-xl font-bold text-text relative z-10">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-text-secondary leading-relaxed relative z-10">{description}</p>
      {action && <div className="mt-8 relative z-10 font-bold">{action}</div>}
    </div>
  );
}
