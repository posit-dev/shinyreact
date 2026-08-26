import { type ShinyClass } from "@posit/shiny/srcts/types/src/shiny";
import { type ShinyMessageRegistry } from "./message-registry";
import { type ShinyReactRegistry } from "./react-registry";
export { ImageOutput } from "./ImageOutput";
export { MISSING } from "./missing";
export type { MISSING as MISSINGType } from "./missing";
export type { OutputStatus, ErrorsMessageValue } from "./output-registry";
export { ShinyReactComponentElement } from "./ShinyReactComponentElement";
export { useSetShinyInput, useShinyBusy, useShinyInitialized, useShinyInput, useShinyInputValue, useShinyMessageHandler, useShinyOutputStatus, useShinyOutputValue, } from "./use-shiny";
export { ShinyModuleProvider, useShinyModuleNamespace, } from "./ShinyModuleContext";
export type ShinyClassExtended = ShinyClass & {
    reactRegistry: ShinyReactRegistry;
    messageRegistry: ShinyMessageRegistry;
};
declare global {
    interface Window {
        Shiny?: ShinyClassExtended;
    }
}
