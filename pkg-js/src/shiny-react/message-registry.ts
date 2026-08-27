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
    // Publish here too, not only from initializeMessageRegistry(): that runs
    // once during shinyreact's init, which can happen before Shiny exists, and
    // it has no retry. This way the window property is set whenever the
    // dispatcher actually gets installed.
    shiny.messageRegistry = this;
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
 * Initialize the global message registry and make it available on window.Shiny
 * This function should be called after Shiny is initialized
 */
export function initializeMessageRegistry(): void {
  const shiny = getShiny();
  if (!shiny) {
    return;
  }
  shiny.messageRegistry = messageRegistry;
}

export { messageRegistry, ShinyMessageRegistry };
