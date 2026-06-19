import { Skeleton } from "./Skeleton";

export function DashboardSkeleton() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 py-8 animate-fade-in w-full">
      {/* Banner Skeleton */}
      <Skeleton className="h-40 w-full rounded-[24px]" />

      {/* Metrics Row */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Skeleton className="h-32 rounded-[20px]" />
        <Skeleton className="h-32 rounded-[20px]" />
        <Skeleton className="h-32 rounded-[20px] sm:col-span-2 lg:col-span-1" />
      </div>

      {/* Main Grid Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Skeleton className="h-80 rounded-[24px]" />
          <Skeleton className="h-64 rounded-[24px]" />
        </div>
        <div className="space-y-6">
          <Skeleton className="h-64 rounded-[24px]" />
          <Skeleton className="h-64 rounded-[24px]" />
        </div>
      </div>
    </div>
  );
}
