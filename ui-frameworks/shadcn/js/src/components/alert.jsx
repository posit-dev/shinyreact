import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

// --- shadcn source (adapted from TS) ---
// shadcn's Alert reserves a leading-icon column via `grid grid-cols-[0_1fr]` +
// `col-start-2` on the title/description. These bridges never render an icon, so
// that grid only causes the content column to collapse. We keep cva for variant
// colors (the part that matters) but use a plain block layout instead of the
// icon grid.

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        destructive:
          "bg-card text-destructive *:data-[slot=alert-description]:text-destructive/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

function Alert({ className, variant, ...props }) {
  return (
    <div data-slot="alert" role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
  );
}

function AlertTitle({ className, ...props }) {
  return (
    <div
      data-slot="alert-title"
      className={cn("mb-1 font-medium leading-none tracking-tight", className)}
      {...props}
    />
  );
}

function AlertDescription({ className, ...props }) {
  return (
    <div
      data-slot="alert-description"
      className={cn("text-sm text-muted-foreground [&_p]:leading-relaxed", className)}
      {...props}
    />
  );
}

// --- shinyreact bridge ---
// Display-only. Props: description (str), title (str, optional),
//   variant ("default" | "destructive"), className (str, optional override).

function ShinyAlert({ element }) {
  const { title, description, variant = "default", className } = element.props;
  return (
    <Alert variant={variant} className={className}>
      {title && <AlertTitle>{title}</AlertTitle>}
      <AlertDescription>
        <p>{description}</p>
      </AlertDescription>
    </Alert>
  );
}

export { ShinyAlert as Alert };
