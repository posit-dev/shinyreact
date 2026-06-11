import { cn } from "@/lib/utils";

export function Card({ element, children }) {
  const { title, className } = element.props;
  return (
    <div className={cn("rounded-xl border bg-card text-card-foreground shadow-sm", className)}>
      {title && (
        <div className="flex flex-col gap-1.5 px-6 pt-6">
          <div className="text-lg font-semibold leading-none tracking-tight">{title}</div>
        </div>
      )}
      <div className={cn("flex flex-col gap-4 px-6 py-6", title && "pt-4")}>
        {children}
      </div>
    </div>
  );
}
