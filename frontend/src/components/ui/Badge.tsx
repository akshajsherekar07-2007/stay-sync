import * as React from "react";
import { cn } from "../../lib/utils";
import styles from "./Badge.module.css";

export type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantClass = styles[`variant-${variant}`];
  
  return (
    <div className={cn(styles.badge, variantClass, className)} {...props} />
  );
}

export { Badge };
