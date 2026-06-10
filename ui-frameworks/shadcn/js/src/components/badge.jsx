const variants = {
  default: "bg-primary text-primary-foreground border-transparent",
  secondary: "bg-secondary text-secondary-foreground border-transparent",
  outline: "text-foreground border-border",
};

export function Badge({ element }) {
  const { text, variant = "default" } = element.props;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${variants[variant] ?? variants.default}`}
    >
      {text}
    </span>
  );
}
