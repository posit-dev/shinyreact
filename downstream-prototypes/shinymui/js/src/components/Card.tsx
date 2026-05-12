import { Card as MuiCard, CardContent, CardHeader } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

export function Card({ element, children }: RegisteredComponentProps) {
  const { title } = element.props as { title?: string };
  return (
    <MuiCard variant="outlined">
      {title && <CardHeader title={title} />}
      <CardContent>{children}</CardContent>
    </MuiCard>
  );
}
