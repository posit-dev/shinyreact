import * as React from "react";
import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { Toaster as Sonner, toast } from "sonner";
import { useShinyMessageHandler } from "@/hooks";

// --- shadcn source (converted from TS) ---
// shadcn's version reads the theme from next-themes. This project has no theme
// provider, so the theme is a plain prop (default "system").

function Toaster({ theme = "system", ...props }) {
  return (
    <Sonner
      theme={theme}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={{
        "--normal-bg": "var(--popover)",
        "--normal-text": "var(--popover-foreground)",
        "--normal-border": "var(--border)",
        "--border-radius": "var(--radius)",
      }}
      {...props}
    />
  );
}

// --- shinyreact bridge ---
// A toast host. Unlike every other component, this has NO trigger and NO input:
// the server PUSHES toasts to it via send_message(). This is the imperative /
// message-handler pattern — the inverse of an input. Mount it once anywhere in
// the page; it renders nothing visible until a message arrives.
//
// Props:
//   message_type (str) — the send_message type to listen for (default "toast").
//   position (str)     — sonner position, e.g. "bottom-right" (default).
//
// Server: send_message(session, "toast", {
//   "message": "Saved!", "description": "...", "type": "success", "duration": 4000
// })
// type ∈ "success" | "info" | "warning" | "error" | "loading" | "default".

function ShinyToaster({ element }) {
  const { message_type = "toast", position = "bottom-right" } = element.props;

  useShinyMessageHandler(message_type, (data) => {
    const { message, description, type = "default", duration } = data ?? {};
    const opts = {};
    if (description) opts.description = description;
    if (duration != null) opts.duration = duration;

    const fn =
      type === "success" ? toast.success
      : type === "info" ? toast.info
      : type === "warning" ? toast.warning
      : type === "error" ? toast.error
      : type === "loading" ? toast.loading
      : toast;
    fn(message, opts);
  });

  return <Toaster position={position} />;
}

export { ShinyToaster as Toaster };
