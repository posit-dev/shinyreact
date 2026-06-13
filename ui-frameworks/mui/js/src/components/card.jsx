import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";

// --- shinyreact bridge ---
// Container: wraps children in an MUI Card with an optional header title.
function ShinyCard({ element, children }) {
  const { title, className } = element.props;
  return (
    <Card className={className}>
      {title && <CardHeader title={title} />}
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export { ShinyCard as Card };
