/**
 * ShinyMessageRegistry manages custom message handlers for React components.
 *
 * This registry provides a centralized system for handling custom messages from
 * the Shiny server, with proper React lifecycle management including automatic
 * cleanup when components unmount.
 *
 * The registry uses a single dispatcher pattern where all messages are sent to
 * "shinyReactMessage" and then routed to the appropriate handlers based on
 * type. This allows multiple components to listen to the same message type and
 * ensures proper cleanup when handlers are no longer needed.
 */
declare class ShinyMessageRegistry {
    private messageHandlers;
    private initialized;
    /**
     * Initialize the message registry by registering the single dispatcher
     * with Shiny's custom message handler system.
     */
    init(): void;
    /**
     * Add a message handler for the specified message type.
     *
     * @param messageType The type/name of the message to listen for
     * @param handler The function to call when a message of this type is received
     */
    addHandler(messageType: string, handler: (data: any) => void): void;
    /**
     * Remove a message handler for the specified message type.
     *
     * @param messageType The type/name of the message
     * @param handler The handler function to remove
     */
    removeHandler(messageType: string, handler: (data: any) => void): void;
    /**
     * Dispatch a message to all registered handlers for the given type.
     *
     * @param messageType The type of message to dispatch
     * @param data The message data to pass to handlers
     */
    private dispatchMessage;
    /**
     * Get the number of handlers registered for a specific message type.
     * Useful for debugging and testing.
     *
     * @param messageType The message type to check
     * @returns The number of handlers registered for this type
     */
    getHandlerCount(messageType: string): number;
    /**
     * Get all message types that currently have registered handlers.
     * Useful for debugging and testing.
     *
     * @returns Array of message types with active handlers
     */
    getActiveMessageTypes(): string[];
}
declare const messageRegistry: ShinyMessageRegistry;
/**
 * Initialize the global message registry and make it available on window.Shiny
 * This function should be called after Shiny is initialized
 */
export declare function initializeMessageRegistry(): void;
export { messageRegistry, ShinyMessageRegistry };
