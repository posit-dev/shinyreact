export function Alert({ element }) {
  const { title, description, variant = "default" } = element.props;
  const isDestructive = variant === "destructive";
  return (
    <div
      role="alert"
      className={`relative w-full rounded-lg border px-4 py-3 text-sm ${isDestructive ? "border-destructive/50 text-destructive" : "border-border bg-background text-foreground"}`}
    >
      {title && <div className="mb-1 font-medium leading-none tracking-tight">{title}</div>}
      <div>{description}</div>
    </div>
  );
}
