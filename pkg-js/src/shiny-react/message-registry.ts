/* eslint-disable @typescript-eslint/no-explicit-any */

import { getShiny } from "./get-shiny";

/**
 * ShinyMessageRegistry manages custom message handlers for React components.
 *
 * This registry provides a centralized system for handling custom messages from
 * the Shiny server, with proper React lifecycle management including automatic
 * cleanup when components unmount.
 *
 * The registry uses a single dispatcher pattern where all messages are sent to
 * "shinyReactMessage" and then routed to the appropriate handlers based on
 * the message id. This allows multiple components to listen to the same message
 * id and ensures proper cleanup when handlers are no longer needed.
 */
class ShinyMessageRegistry {
  private messageHandlers: Map<string, Set<(data: any) => void>> = new Map();
  private initialized = false;

  /**
   * Initialize the message registry by registering the single dispatcher
   * with Shiny's custom message handler system.
   */
  init() {
    if (this.initialized) {
      return;
    }

    const shiny = getShiny();
    if (!shiny) {
      return;
    }

    shiny.addCustomMessageHandler(
      "shinyReactMessage",
      (msg: { id: string; data: any }) => {
        this.dispatchMessage(msg.id, msg.data);
      },
    );
    this.initialized = true;
  }

  /**
   * Add a message handler for the specified message id.
   *
   * @param messageId The id of the message to listen for
   * @param handler The function to call when a message with this id is received
   */
  addHandler(messageId: string, handler: (data: any) => void) {
    this.init(); // Ensure registry is initialized

    if (!this.messageHandlers.has(messageId)) {
      this.messageHandlers.set(messageId, new Set());
    }
    this.messageHandlers.get(messageId)!.add(handler);
  }

  /**
   * Remove a message handler for the specified message id.
   *
   * @param messageId The id of the message
   * @param handler The handler function to remove
   */
  removeHandler(messageId: string, handler: (data: any) => void) {
    const handlers = this.messageHandlers.get(messageId);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.messageHandlers.delete(messageId);
      }
    }
  }

  /**
   * Dispatch a message to all registered handlers for the given id.
   *
   * @param messageId The id of the message to dispatch
   * @param data The message data to pass to handlers
   */
  private dispatchMessage(messageId: string, data: any) {
    const handlers = this.messageHandlers.get(messageId);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  /**
   * Get the number of handlers registered for a specific message id.
   * Useful for debugging and testing.
   *
   * @param messageId The message id to check
   * @returns The number of handlers registered for this id
   */
  getHandlerCount(messageId: string): number {
    const handlers = this.messageHandlers.get(messageId);
    return handlers ? handlers.size : 0;
  }

  /**
   * Get all message ids that currently have registered handlers.
   * Useful for debugging and testing.
   *
   * @returns Array of message ids with active handlers
   */
  getActiveMessageIds(): string[] {
    return Array.from(this.messageHandlers.keys());
  }
}

// Global message registry instance
const messageRegistry = new ShinyMessageRegistry();

// Note: Global Window interface is extended in use-shiny.ts to avoid conflicts

/**
 * The message registry for this *page*.
 *
 * Deliberately page-scoped rather than module-scoped, and the one place that
 * attaches it to `window.Shiny`. Two copies of this library can be on a page
 * today — the page entry points serve shinyreact.js unless an npm-tier app
 * passes `shinyreact_js="client"` (#217) — and each copy has its own module
 * singleton. Two
 * registries would mean two `addCustomMessageHandler("shinyReactMessage")`
 * calls, and Shiny gives us one dispatcher slot per message type: whichever
 * behaviour it has (silently replacing the first, or throwing), one copy's
 * handlers stop receiving messages. Sharing through Shiny's own object is what
 * keeps a single dispatcher and a single handler map.
 *
 * `??=` so the first caller wins and later callers adopt it. Reading through
 * this accessor instead of `shiny.messageRegistry` directly is also what fixes
 * the crash it replaced: the property could be unset when a hook ran, because
 * the old eager publish was a no-op if Shiny had not loaded yet.
 *
 * Handlers registered before Shiny exists live on the module singleton, which
 * becomes the page registry if it attaches first. If a *different* copy
 * attached first, those early handlers stay on the local instance — an
 * accepted edge, since hooks only register after Shiny reports initialized.
 */
export function getMessageRegistry(): ShinyMessageRegistry {
  const shiny = getShiny();
  if (!shiny) {
    return messageRegistry;
  }
  return (shiny.messageRegistry ??= messageRegistry);
}

/**
 * Attach the registry to `window.Shiny` eagerly, during shinyreact's one-time
 * init. A no-op without Shiny; `getMessageRegistry()` attaches later in that
 * case, so nothing depends on this having run.
 */
export function initializeMessageRegistry(): void {
  if (getShiny()) {
    getMessageRegistry();
  }
}

export { messageRegistry, ShinyMessageRegistry };
