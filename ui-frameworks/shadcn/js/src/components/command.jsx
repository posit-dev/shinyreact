import { Command as CommandPrimitive } from "cmdk";
import { SearchIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useShinyInput } from "shinyreact";
function Command({
  className,
  ...props
}) {
  return <CommandPrimitive
    data-slot="command"
    className={cn(
      "flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground",
      className
    )}
    {...props}
  />;
}
function CommandInput({
  className,
  ...props
}) {
  return <div
    data-slot="command-input-wrapper"
    className="flex h-9 items-center gap-2 border-b px-3"
  ><SearchIcon className="size-4 shrink-0 opacity-50" /><CommandPrimitive.Input
    data-slot="command-input"
    className={cn(
      "flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-hidden placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  /></div>;
}
function CommandList({
  className,
  ...props
}) {
  return <CommandPrimitive.List
    data-slot="command-list"
    className={cn(
      "max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto",
      className
    )}
    {...props}
  />;
}
function CommandEmpty({
  ...props
}) {
  return <CommandPrimitive.Empty
    data-slot="command-empty"
    className="py-6 text-center text-sm"
    {...props}
  />;
}
function CommandGroup({
  className,
  ...props
}) {
  return <CommandPrimitive.Group
    data-slot="command-group"
    className={cn(
      "overflow-hidden p-1 text-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground",
      className
    )}
    {...props}
  />;
}
function CommandSeparator({
  className,
  ...props
}) {
  return <CommandPrimitive.Separator
    data-slot="command-separator"
    className={cn("-mx-1 h-px bg-border", className)}
    {...props}
  />;
}
function CommandItem({
  className,
  ...props
}) {
  return <CommandPrimitive.Item
    data-slot="command-item"
    className={cn(
      "relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50 data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 [&_svg:not([class*='text-'])]:text-muted-foreground",
      className
    )}
    {...props}
  />;
}
function CommandShortcut({
  className,
  ...props
}) {
  return <span
    data-slot="command-shortcut"
    className={cn(
      "ml-auto text-xs tracking-widest text-muted-foreground",
      className
    )}
    {...props}
  />;
}

// --- shinyreact bridge ---
function ShinyCommand({ element }) {
  const {
    input_id,
    items = [],
    placeholder = "Search...",
    empty_label = "No results found.",
    className,
  } = element.props;
  const [, setValue] = useShinyInput(input_id, null);

  const grouped = items.reduce((acc, item) => {
    const g = item.group ?? "";
    if (!acc[g]) acc[g] = [];
    acc[g].push(item);
    return acc;
  }, {});

  return (
    <Command className={className}>
      <CommandInput placeholder={placeholder} />
      <CommandList>
        <CommandEmpty>{empty_label}</CommandEmpty>
        {Object.entries(grouped).map(([group, groupItems]) => (
          <CommandGroup key={group} heading={group || undefined}>
            {groupItems.map((item) => (
              <CommandItem
                key={item.value}
                value={item.value}
                onSelect={() => setValue(item.value)}
              >
                {item.label}
              </CommandItem>
            ))}
          </CommandGroup>
        ))}
      </CommandList>
    </Command>
  );
}

export { ShinyCommand as Command };
