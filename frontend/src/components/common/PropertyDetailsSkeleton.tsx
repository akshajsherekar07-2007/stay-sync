import { Skeleton } from "./Skeleton";

export function PropertyDetailsSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 w-full animate-fade-in">
      {/* Back button */}
      <Skeleton className="h-5 w-32 mb-6" />

      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
        <div className="space-y-3">
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-28 rounded-full" />
          </div>
          <Skeleton className="h-10 w-96 rounded-lg" />
          <Skeleton className="h-4 w-72 rounded-md" />
        </div>
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-8">
          {/* Gallery */}
          <div className="space-y-3">
            <Skeleton className="w-full aspect-video rounded-2xl" />
            <div className="flex gap-2">
              <Skeleton className="w-24 aspect-[16/10] rounded-xl" />
              <Skeleton className="w-24 aspect-[16/10] rounded-xl" />
              <Skeleton className="w-24 aspect-[16/10] rounded-xl" />
            </div>
          </div>

          {/* About */}
          <Skeleton className="h-48 w-full rounded-[24px]" />

          {/* Amenities */}
          <Skeleton className="h-32 w-full rounded-[24px]" />

          {/* Floor/Room Selector */}
          <Skeleton className="h-96 w-full rounded-[24px]" />
        </div>

        {/* Right 1 Column */}
        <div className="space-y-6">
          <Skeleton className="h-64 w-full rounded-[24px]" />
          <Skeleton className="h-40 w-full rounded-[24px]" />
        </div>
      </div>
    </div>
  );
}
