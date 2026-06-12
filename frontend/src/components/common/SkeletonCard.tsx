import * as React from "react";
import { Card, CardHeader, CardContent, CardFooter } from "../ui/Card";
import { Skeleton } from "./Skeleton";

export interface SkeletonCardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SkeletonCard({ className, ...props }: SkeletonCardProps) {
  return (
    <Card className={className} {...props}>
      <div className="relative w-full aspect-video rounded-t-lg overflow-hidden">
        <Skeleton className="absolute inset-0 rounded-none" />
      </div>
      <CardHeader className="space-y-2">
        <Skeleton className="h-5 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
      </CardContent>
      <CardFooter className="border-t border-border/50 pt-4 flex justify-between items-center">
        <Skeleton className="h-5 w-1/4" />
        <Skeleton className="h-9 w-1/3" />
      </CardFooter>
    </Card>
  );
}
