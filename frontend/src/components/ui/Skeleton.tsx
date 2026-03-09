interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className = '', variant = 'rectangular', width, height }: SkeletonProps) {
  const baseClasses = 'skeleton';

  const variantClasses: Record<string, string> = {
    text: 'h-4 w-full',
    circular: 'rounded-full',
    rectangular: 'rounded',
  };

  const style = width !== undefined || height !== undefined
    ? {
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }
    : undefined;

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

export function MessageSkeleton() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[70%]">
        <Skeleton variant="text" width={200} className="mb-2" />
        <Skeleton variant="text" width={150} className="mb-2" />
        <Skeleton variant="text" width={180} />
      </div>
    </div>
  );
}

export function DocumentSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton variant="text" width={200} height={20} className="mb-2" />
          <div className="flex items-center gap-4">
            <Skeleton variant="text" width={100} />
            <Skeleton variant="text" width={80} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function DocumentListSkeleton() {
  return (
    <div className="p-6 space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <DocumentSkeleton key={i} />
      ))}
    </div>
  );
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center">
            <Skeleton variant="circular" width={24} height={24} className="mr-3" />
            <div className="flex-1">
              <Skeleton variant="text" width={100} className="mb-1" />
              <Skeleton variant="text" width={60} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function SessionListSkeleton() {
  return (
    <div className="w-64">
      <div className="p-4 border-b">
        <Skeleton variant="rectangular" height={40} />
      </div>
      <div className="p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="mb-4 last:mb-0">
            <Skeleton variant="text" width={140} className="mb-1" />
            <Skeleton variant="text" width={80} />
          </div>
        ))}
      </div>
    </div>
  );
}
