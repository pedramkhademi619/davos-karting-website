/** Grey placeholder shapes that stand where content will be, instead of a spinner: the page keeps its layout while it loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`skeleton block ${className}`} />;
}

type Variant = "cards" | "rows" | "form" | "page";

/**
 * A loading placeholder shaped like what is coming: `cards` (a row of figures and two panels), `rows` (a table or list),
 * `form` (labelled fields), `page` (header, tabs and cards: a whole screen). Read by screen readers as "loading".
 */
export function PageSkeleton({ variant = "rows", label = "در حال بارگذاری" }: { variant?: Variant; label?: string }) {
  return (
    <div role="status" className="space-y-5">
      <span className="sr-only">{label}</span>
      {variant === "page" && (
        <div className="space-y-4">
          <Skeleton className="h-9 w-56 rounded-xl" />
          <Skeleton className="h-4 w-80 max-w-full rounded-lg" />
          <div className="flex gap-2 pt-2">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-11 w-28 rounded-full" />
            ))}
          </div>
        </div>
      )}
      {(variant === "cards" || variant === "page") && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32 rounded-3xl" />
            ))}
          </div>
          <div className="grid gap-5 lg:grid-cols-2">
            <Skeleton className="h-56 rounded-3xl" />
            <Skeleton className="h-56 rounded-3xl" />
          </div>
        </>
      )}
      {variant === "rows" && (
        <div className="space-y-3">
          <Skeleton className="h-11 rounded-2xl" />
          {[0, 1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-14 rounded-2xl" />
          ))}
        </div>
      )}
      {variant === "form" && (
        <div className="space-y-5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-40 rounded-lg" />
              <Skeleton className="h-12 rounded-2xl" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
