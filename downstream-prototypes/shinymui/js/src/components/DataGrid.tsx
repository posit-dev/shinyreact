import { DataGrid as MuiDataGrid, type GridColDef } from "@mui/x-data-grid";
import { Box } from "@mui/material";
import type { RegisteredComponentProps } from "../types";

const { useShinyOutputValue } = window.shinyreact;

interface GridPayload {
  rows: Array<Record<string, unknown> & { id: string | number }>;
  columns: GridColDef[];
}

export function DataGrid({ element }: RegisteredComponentProps) {
  const { output_id, height } = element.props as {
    output_id: string;
    height?: number;
  };

  const payload = useShinyOutputValue<GridPayload | null>(output_id, null);

  if (!payload) {
    return <Box sx={{ height: height ?? 400 }}>Loading…</Box>;
  }

  return (
    <Box sx={{ height: height ?? 400, width: "100%" }}>
      <MuiDataGrid rows={payload.rows} columns={payload.columns} />
    </Box>
  );
}
