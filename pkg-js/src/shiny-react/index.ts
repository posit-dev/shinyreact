// Main exports for shiny-react JavaScript library
import { type ShinyClass } from "@posit/shiny/srcts/types/src/shiny";
import { type ShinyMessageRegistry } from "./message-registry";
import { type ShinyReactRegistry } from "./react-registry";

export { ImageOutput } from "./ImageOutput";
export { MISSING } from "./missing";
export type { MISSING as MISSINGType } from "./missing";
export type { OutputStatus, ErrorsMessageValue } from "./output-registry";
// ShinyReactComponentElement is not exported today. It is the base class for
// custom elements that mount a React island inside server-rendered HTML — the
// inverse of the ui.tsx pattern, where the server emits no UI. Nothing in the
// repo subclasses it. Re-enable this export (and the ones in global.ts and
// npm.ts) when partial React app support lands, i.e. when a traditional Shiny
// page can host React components.
// export { ShinyReactComponentElement } from "./ShinyReactComponentElement";
export {
  useSetShinyInput,
  useShinyBusy,
  useShinyInitialized,
  useShinyInput,
  useShinyInputValue,
  useShinyMessageHandler,
  useShinyOutputError,
  useShinyOutputStatus,
  useShinyOutputValue,
} from "./use-shiny";
export {
  ShinyModuleProvider,
  useShinyModuleNamespace,
} from "./ShinyModuleContext";

export type ShinyClassExtended = ShinyClass & {
  /** Attached on first use by getReactRegistry(); absent before that. */
  reactRegistry?: ShinyReactRegistry;
  /** Attached on first use by getMessageRegistry(); absent before that. */
  messageRegistry?: ShinyMessageRegistry;
};

declare global {
  interface Window {
    Shiny?: ShinyClassExtended;
  }
}
