/**
 * Shared Skeleton loader components for consistent loading states.
 * Usage: <SkeletonLine />, <SkeletonCard />, <SkeletonTable rows={5} cols={4} />
 */

/** A single shimmer line */
export function SkeletonLine({ className = "" }) {
  return (
    <div
      className={`h-4 bg-gray-200 rounded animate-pulse ${className}`}
    />
  );
}

/** A skeleton block for cards / stat boxes */
export function SkeletonCard({ className = "" }) {
  return (
    <div className={`bg-white rounded-xl border p-5 space-y-3 ${className}`}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gray-200 animate-pulse" />
        <div className="flex-1 space-y-2">
          <SkeletonLine className="w-1/3" />
          <SkeletonLine className="w-1/2 h-6" />
        </div>
      </div>
    </div>
  );
}

/** Skeleton for a table body */
export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
      {/* Fake header */}
      <div className="flex gap-4 px-5 py-3 border-b bg-gray-50">
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonLine key={i} className="flex-1 h-3" />
        ))}
      </div>
      {/* Fake rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-5 py-4 border-b last:border-0">
          {Array.from({ length: cols }).map((_, j) => (
            <SkeletonLine
              key={j}
              className={`flex-1 ${j === 0 ? "w-2/5" : ""}`}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Full-page loading skeleton for dashboard-style pages */
export function SkeletonDashboard() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Stat cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-xl border p-5 space-y-3">
            <div className="flex items-center justify-between">
              <SkeletonLine className="w-1/2 h-3" />
              <div className="w-8 h-8 rounded-lg bg-gray-200" />
            </div>
            <SkeletonLine className="w-2/3 h-7" />
            <SkeletonLine className="w-1/3 h-3" />
          </div>
        ))}
      </div>
      {/* Chart placeholder */}
      <div className="bg-white rounded-xl border p-5">
        <SkeletonLine className="w-1/4 h-4 mb-5" />
        <div className="h-48 bg-gray-100 rounded-lg" />
      </div>
      {/* Table */}
      <SkeletonTable rows={4} cols={5} />
    </div>
  );
}

/** Empty state component */
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <Icon size={24} className="text-gray-400" />
        </div>
      )}
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-400 max-w-xs mb-4">{description}</p>}
      {action}
    </div>
  );
}
