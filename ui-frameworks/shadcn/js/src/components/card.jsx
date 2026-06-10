export function Card({ element, children }) {
  const { title } = element.props;
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow">
      {title && (
        <div className="flex flex-col space-y-1.5 p-4 pb-2">
          <h3 className="font-semibold leading-none tracking-tight">{title}</h3>
        </div>
      )}
      <div className={`p-4 ${title ? "pt-2" : ""} flex flex-col gap-4`}>
        {children}
      </div>
    </div>
  );
}
