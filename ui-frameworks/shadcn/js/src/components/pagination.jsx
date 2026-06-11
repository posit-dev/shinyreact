import * as React from "react";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MoreHorizontalIcon
} from "lucide-react";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/lib/button-base";
import { useShinyInput } from "@/hooks";
function Pagination({ className, ...props }) {
  return <nav
    role="navigation"
    aria-label="pagination"
    data-slot="pagination"
    className={cn("mx-auto flex w-full justify-center", className)}
    {...props}
  />;
}
function PaginationContent({
  className,
  ...props
}) {
  return <ul
    data-slot="pagination-content"
    className={cn("flex flex-row items-center gap-1", className)}
    {...props}
  />;
}
function PaginationItem({ ...props }) {
  return <li data-slot="pagination-item" {...props} />;
}
function PaginationLink({
  className,
  isActive,
  size = "icon",
  ...props
}) {
  return <a
    aria-current={isActive ? "page" : void 0}
    data-slot="pagination-link"
    data-active={isActive}
    className={cn(
      buttonVariants({
        variant: isActive ? "outline" : "ghost",
        size
      }),
      className
    )}
    {...props}
  />;
}
function PaginationPrevious({
  className,
  ...props
}) {
  return <PaginationLink
    aria-label="Go to previous page"
    size="default"
    className={cn("gap-1 px-2.5 sm:pl-2.5", className)}
    {...props}
  ><ChevronLeftIcon /><span className="hidden sm:block">Previous</span></PaginationLink>;
}
function PaginationNext({
  className,
  ...props
}) {
  return <PaginationLink
    aria-label="Go to next page"
    size="default"
    className={cn("gap-1 px-2.5 sm:pr-2.5", className)}
    {...props}
  ><span className="hidden sm:block">Next</span><ChevronRightIcon /></PaginationLink>;
}
function PaginationEllipsis({
  className,
  ...props
}) {
  return <span
    aria-hidden
    data-slot="pagination-ellipsis"
    className={cn("flex size-9 items-center justify-center", className)}
    {...props}
  ><MoreHorizontalIcon className="size-4" /><span className="sr-only">More pages</span></span>;
}

// --- shinyreact bridge ---
// @shiny type=Input children=false props=input_id:str,total_pages:int=10,current:int=1,show_ellipsis:bool=True,class_:str=None
function ShinyPagination({ element }) {
  const {
    input_id,
    total_pages = 1,
    current: initialPage = 1,
    show_ellipsis = true,
    className,
  } = element.props;

  const [page, setPage] = useShinyInput(input_id, initialPage);

  function getPageNumbers() {
    if (!show_ellipsis || total_pages <= 7) {
      return Array.from({ length: total_pages }, (_, i) => i + 1);
    }
    const pages = [1];
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(total_pages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < total_pages - 2) pages.push("...");
    pages.push(total_pages);
    return pages;
  }

  const pages = getPageNumbers();

  return (
    <Pagination className={className}>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            onClick={(e) => { e.preventDefault(); if (page > 1) setPage(page - 1); }}
            className={page <= 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
          />
        </PaginationItem>
        {pages.map((p, i) =>
          p === "..." ? (
            <PaginationItem key={`ellipsis-${i}`}>
              <PaginationEllipsis />
            </PaginationItem>
          ) : (
            <PaginationItem key={p}>
              <PaginationLink
                isActive={p === page}
                onClick={(e) => { e.preventDefault(); setPage(p); }}
                className="cursor-pointer"
              >
                {p}
              </PaginationLink>
            </PaginationItem>
          )
        )}
        <PaginationItem>
          <PaginationNext
            onClick={(e) => { e.preventDefault(); if (page < total_pages) setPage(page + 1); }}
            className={page >= total_pages ? "pointer-events-none opacity-50" : "cursor-pointer"}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}

export { ShinyPagination as Pagination };
