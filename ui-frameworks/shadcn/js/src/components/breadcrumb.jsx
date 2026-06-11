import * as React from "react";
import { ChevronRight, MoreHorizontal } from "lucide-react";
import { Slot } from "radix-ui";
import { cn } from "@/lib/utils";
function Breadcrumb({ ...props }) {
  return <nav aria-label="breadcrumb" data-slot="breadcrumb" {...props} />;
}
function BreadcrumbList({ className, ...props }) {
  return <ol
    data-slot="breadcrumb-list"
    className={cn(
      "flex flex-wrap items-center gap-1.5 text-sm break-words text-muted-foreground sm:gap-2.5",
      className
    )}
    {...props}
  />;
}
function BreadcrumbItem({ className, ...props }) {
  return <li
    data-slot="breadcrumb-item"
    className={cn("inline-flex items-center gap-1.5", className)}
    {...props}
  />;
}
function BreadcrumbLink({
  asChild,
  className,
  ...props
}) {
  const Comp = asChild ? Slot.Root : "a";
  return <Comp
    data-slot="breadcrumb-link"
    className={cn("transition-colors hover:text-foreground", className)}
    {...props}
  />;
}
function BreadcrumbPage({ className, ...props }) {
  return <span
    data-slot="breadcrumb-page"
    role="link"
    aria-disabled="true"
    aria-current="page"
    className={cn("font-normal text-foreground", className)}
    {...props}
  />;
}
function BreadcrumbSeparator({
  children,
  className,
  ...props
}) {
  return <li
    data-slot="breadcrumb-separator"
    role="presentation"
    aria-hidden="true"
    className={cn("[&>svg]:size-3.5", className)}
    {...props}
  >{children ?? <ChevronRight />}</li>;
}
function BreadcrumbEllipsis({
  className,
  ...props
}) {
  return <span
    data-slot="breadcrumb-ellipsis"
    role="presentation"
    aria-hidden="true"
    className={cn("flex size-9 items-center justify-center", className)}
    {...props}
  ><MoreHorizontal className="size-4" /><span className="sr-only">More</span></span>;
}

// --- shinyreact bridge ---
// Display-only breadcrumb trail driven by an items array. The last item renders
// as the current page; earlier items with an href render as links.
// Props: items ({label, href?}[]), className. No input.

function ShinyBreadcrumb({ element }) {
  const { items = [], className } = element.props;
  return (
    <Breadcrumb className={className}>
      <BreadcrumbList>
        {items.map((it, i) => (
          <React.Fragment key={i}>
            <BreadcrumbItem>
              {it.href && i < items.length - 1 ? (
                <BreadcrumbLink href={it.href}>{it.label}</BreadcrumbLink>
              ) : (
                <BreadcrumbPage>{it.label}</BreadcrumbPage>
              )}
            </BreadcrumbItem>
            {i < items.length - 1 && <BreadcrumbSeparator />}
          </React.Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

export { ShinyBreadcrumb as Breadcrumb };
