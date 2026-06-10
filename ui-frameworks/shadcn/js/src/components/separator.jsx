export function Separator({ element }) {
  const { orientation = "horizontal" } = element.props;
  return (
    <div
      role="separator"
      className={`shrink-0 bg-border ${orientation === "vertical" ? "h-full w-px" : "h-px w-full"}`}
    />
  );
}
