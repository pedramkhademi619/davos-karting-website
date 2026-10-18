import { PageSkeleton } from "@/components/ui/skeleton";

/** Shown at once while a page of the public site is being prepared on the server (instead of a blank wait). */
export default function Loading() {
  return (
    <div className="container-page py-10 md:py-14">
      <PageSkeleton variant="page" />
    </div>
  );
}
