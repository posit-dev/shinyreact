import { InputRegistry } from "./input-registry";
import { OutputRegistry } from "./output-registry";
export interface ShinyReactRegistry {
    inputs: InputRegistry;
    outputs: OutputRegistry;
}
declare let reactRegistry: ShinyReactRegistry | undefined;
/**
 * Initialize the global react registry and make it available on window.Shiny
 * This function should be called after Shiny is initialized
 */
export declare function initializeReactRegistry(): void;
/**
 * Get the react registry, whether it's attached to window.Shiny or standalone
 */
export declare function getReactRegistry(): ShinyReactRegistry;
export { reactRegistry };
