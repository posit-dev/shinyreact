import * as React from "react";
import { cva } from "class-variance-authority";
import { Tabs as TabsPrimitive } from "radix-ui";
import { cn } from "@/lib/utils";
import { useShinyInput } from "@/hooks";

// --- shadcn source (converted from TS) ---

const tabsListVariants = cva(
  "group/tabs-list inline-flex w-fit items-center justify-center rounded-lg p-[3px] text-muted-foreground group-data-[orientation=horizontal]/tabs:h-9 group-data-[orientation=vertical]/tabs:h-fit group-data-[orientation=vertical]/tabs:flex-col",
  {
    variants: {
      variant: {
        default: "bg-muted",
        line: "gap-1 bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

function Tabs({ className, orientation = "horizontal", ...props }) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      data-orientation={orientation}
      orientation={orientation}
      className={cn("group/tabs flex gap-2 data-[orientation=horizontal]:flex-col", className)}
      {...props}
    />
  );
}

function TabsList({ className, variant = "default", ...props }) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      data-variant={variant}
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    />
  );
}

function TabsTrigger({ className, ...props }) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "relative inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap text-foreground/60 transition-all hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    />
  );
}

function TabsContent({ className, ...props }) {
  return <TabsPrimitive.Content data-slot="tabs-content" className={cn("flex-1 outline-none", className)} {...props} />;
}

// --- shinyreact bridge ---
// Hybrid component: tab metadata is a `tabs` prop array (the triggers); panel
// content is free-form children, matched to tabs *positionally* (the Nth child
// renders in the Nth tab). This pairs a structured prop array with free-form
// children — the bridge does not read child props, only their order.
//
// Props:
//   input_id (str)            — active tab value. Two-way: server can read it
//                               and the client updates it on tab change.
//   tabs ({value,label}[])    — the tab triggers, in order.
//   selected (str, optional)  — initially active tab (defaults to first).
// Children: one panel per tab, in the same order as `tabs`.

function ShinyTabs({ element, children }) {
  const { input_id, tabs = [], selected, className } = element.props;
  const firstVal = tabs.length > 0 ? tabs[0].value : "";
  const [value, setValue] = useShinyInput(input_id, selected ?? firstVal);
  const panels = React.Children.toArray(children);

  return (
    <Tabs value={value} onValueChange={setValue} className={cn("w-full", className)}>
      <TabsList>
        {tabs.map((t) => (
          <TabsTrigger key={t.value} value={t.value}>
            {t.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs.map((t, i) => (
        <TabsContent key={t.value} value={t.value}>
          {panels[i]}
        </TabsContent>
      ))}
    </Tabs>
  );
}

export { ShinyTabs as Tabs };
