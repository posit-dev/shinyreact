import React from "react";
import { Button as MuiButton } from "@mui/material";
import * as MuiIcons from "@mui/icons-material";
import type { RegisteredComponentProps } from "../types";

const { useShinyInput } = window.shinyreact;

type IconName = keyof typeof MuiIcons;

function renderIcon(name: unknown): React.ReactNode {
  if (typeof name !== "string") return undefined;
  const Icon = MuiIcons[name as IconName];
  if (!Icon) {
    console.warn(`[shinymui] unknown icon "${name}"`);
    return undefined;
  }
  return React.createElement(Icon as React.ComponentType);
}

export function Button({ element }: RegisteredComponentProps) {
  const {
    label,
    input_id,
    variant,
    color,
    start_icon,
    end_icon,
  } = element.props as {
    label: string;
    input_id: string;
    variant?: "text" | "contained" | "outlined";
    color?: "primary" | "secondary" | "success" | "error";
    start_icon?: string;
    end_icon?: string;
  };

  const [count, setCount] = useShinyInput<number>(input_id, 0, {
    debounceMs: 0,
    priority: "event",
  });

  return (
    <MuiButton
      variant={variant ?? "contained"}
      color={color ?? "primary"}
      startIcon={renderIcon(start_icon)}
      endIcon={renderIcon(end_icon)}
      onClick={() => setCount((count ?? 0) + 1)}
    >
      {label}
    </MuiButton>
  );
}
