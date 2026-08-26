import React from "react";
import * as ReactDOM from "react-dom/client";
import { ShinyOutput } from "./shiny-output";
import { useSetShinyInput, useShinyBusy, useShinyInput, useShinyInputValue, useShinyOutputStatus, useShinyOutputValue, useShinyMessageHandler, useShinyInitialized, ImageOutput, MISSING, ShinyModuleProvider, ShinyReactComponentElement } from "./shiny-react";
declare global {
    interface Window {
        shinyreact: {
            useSetShinyInput: typeof useSetShinyInput;
            useShinyBusy: typeof useShinyBusy;
            useShinyInput: typeof useShinyInput;
            useShinyInputValue: typeof useShinyInputValue;
            useShinyOutputStatus: typeof useShinyOutputStatus;
            useShinyOutputValue: typeof useShinyOutputValue;
            useShinyMessageHandler: typeof useShinyMessageHandler;
            useShinyInitialized: typeof useShinyInitialized;
            ImageOutput: typeof ImageOutput;
            MISSING: typeof MISSING;
            ShinyModuleProvider: typeof ShinyModuleProvider;
            ShinyReactComponentElement: typeof ShinyReactComponentElement;
            ShinyOutput: typeof ShinyOutput;
            React: typeof React;
            ReactDOM: typeof ReactDOM;
        };
    }
}
/**
 * Expose the public global API at `window.shinyreact`. Called once at bundle
 * boot. Nothing writes the namespace before the bundle runs — server state
 * arrives via the `#shinyreact-config` JSON script tag, not the global — so
 * this is a plain assignment.
 */
export declare function installGlobal(): void;
