import * as React from "react";
import { Card, CardContent } from "../ui/Card";
import { Skeleton } from "./Skeleton";

export interface SkeletonCardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SkeletonCard({ className, ...props }: SkeletonCardProps) {
  return (
    <Card className={`rounded-[24px] overflow-hidden border-none bg-card shadow-sm ${className}`} {...props}>
      <div className="relative w-full aspect-video">
        <Skeleton className="absolute inset-0 rounded-none bg-bg-secondary" />
        <div className="absolute top-4 left-4 flex gap-2">
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
      <CardContent className="p-6">
        <div className="flex justify-between items-start gap-4 mb-2">
          <div className="space-y-2 flex-grow">
            <Skeleton className="h-6 w-3/4 rounded-md" />
            <Skeleton className="h-4 w-1/2 rounded-md" />
          </div>
          <Skeleton className="h-8 w-16 rounded-lg shrink-0" />
        </div>
        
        <div className="flex items-center gap-4 mt-6">
          <Skeleton className="h-4 w-16 rounded-md" />
          <Skeleton className="h-4 w-16 rounded-md" />
        </div>
        
        <div className="flex flex-wrap gap-2 mt-4">
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </CardContent>
    </Card>
  );
}
