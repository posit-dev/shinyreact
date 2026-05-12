/* eslint-disable @typescript-eslint/no-explicit-any */
import { type InputRegistry } from "./input-registry";

/**
 * Adopt bookmarked input values into the input registry.
 *
 * Reads `window.shinyreact._restore` (set by a head <script> emitted by
 * Python's `_restore_script_tag`), seeds each entry into `registry` via
 * `add()` so the value is stored without sending to Shiny, and replaces
 * the global with a sentinel `{ "-applied": true, "-values": <appliedMap> }`
 * for DevTools inspection.
 *
 * Idempotent: when called against an already-applied global (the sentinel's
 * "-applied" key is true), it does not re-apply and preserves the snapshot.
 *
 * SECURITY: bookmarked input values arrive in the page HTML source. URL mode
 * already exposes them in the URL; server-stored mode re-exposes them via
 * this script. Apps must not put credentials, tokens, PII, or other
 * sensitive data into inputs that participate in bookmarking.
 */
export function applyRestoredValues(registry: InputRegistry): void {
  const win = (typeof window !== "undefined" ? window : (globalThis as any)) as any;
  const ns = (win.shinyreact = win.shinyreact || {});
  const restore = ns._restore;

  // Null-prototype object for the debug snapshot so an assignment with key
  // "__proto__" or "constructor" cannot clobber the prototype chain. Even
  // though Python emits the payload via `JSON.parse(...)` (which already
  // treats those keys as ordinary properties), the snapshot exposed on
  // `window.shinyreact._restore["-values"]` is constructed from untrusted
  // input ids — defend in depth at the assignment site as well.
  const applied = Object.create(null) as Record<string, unknown>;
  if (restore && typeof restore === "object" && !restore["-applied"]) {
    for (const [id, value] of Object.entries(restore)) {
      registry.add(id, value);
      applied[id] = value;
    }
    ns._restore = { "-applied": true, "-values": applied };
    return;
  }

  if (restore && typeof restore === "object" && restore["-applied"]) {
    // Already applied — preserve the existing snapshot.
    return;
  }

  // No restore data at all — establish the uniform post-init sentinel.
  ns._restore = { "-applied": true, "-values": applied };
}
