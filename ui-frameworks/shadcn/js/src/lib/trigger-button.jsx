export function TriggerButton({ children, ...props }) {
  return (
    <button
      type="button"
      className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 h-9 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
      {...props}
    >
      {children}
    </button>
  );
}
