import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-white shadow hover:bg-primary-dark",
        secondary:
          "border-transparent bg-bg-secondary text-text hover:bg-bg-tertiary",
        destructive:
          "border-transparent bg-danger text-white shadow hover:bg-danger/90",
        outline: "text-text border-border",
        success:
          "border-transparent bg-success text-white shadow hover:bg-success/90",
        warning:
          "border-transparent bg-warning text-white shadow hover:bg-warning/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
