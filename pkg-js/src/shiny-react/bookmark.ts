/* eslint-disable @typescript-eslint/no-explicit-any */
import { type InputRegistry } from "./input-registry";
import {
  assertProtocolCompatible,
  isShinyReactConfigTagRequired,
  readShinyReactConfig,
} from "./config";

/**
 * Adopt bookmarked input values into the input registry.
 *
 * Reads the `restore` payload from the `#shinyreact-config` JSON script tag
 * emitted by the server's page entry points — the only delivery channel.
 * Seeds each entry into `registry` via `add()` so the value is stored
 * without sending to Shiny, and records a sentinel
 * `{ "-applied": true, "-values": <appliedMap> }` at
 * `window.shinyreact._restore` for DevTools inspection. The sentinel is an
 * output only; nothing is ever read from it as restore input.
 *
 * Also performs the protocol handshake: when the config tag carries a
 * `protocolVersion`, the major version must match this client's
 * PROTOCOL_VERSION or an error is thrown naming both versions.
 *
 * Idempotent: when called against an already-applied sentinel (the
 * "-applied" key is true), it does not re-apply and preserves the snapshot.
 *
 * SECURITY: bookmarked input values arrive in the page HTML source. URL mode
 * already exposes them in the URL; server-stored mode re-exposes them via
 * the config tag. Apps must not put credentials, tokens, PII, or other
 * sensitive data into inputs that participate in bookmarking.
 */
export function applyRestoredValues(registry: InputRegistry): void {
  const win = (typeof window !== "undefined" ? window : (globalThis as any)) as any;
  const ns = (win.shinyreact = win.shinyreact || {});
  const existing = ns._restore;

  // Already applied — preserve the existing snapshot.
  if (existing && typeof existing === "object" && existing["-applied"]) {
    return;
  }

  const config = readShinyReactConfig();
  if (config == null && isShinyReactConfigTagRequired()) {
    throw new Error(
      "shinyreact: no #shinyreact-config tag found in this page. The " +
        "@posit/shinyreact client requires a shinyreact server recent " +
        "enough to emit it — upgrade the shinyreact Python/R package.",
    );
  }
  if (config?.protocolVersion) {
    assertProtocolCompatible(config.protocolVersion);
  }
  const restore = config?.restore;

  // Null-prototype object for the debug snapshot so an assignment with key
  // "__proto__" or "constructor" cannot clobber the prototype chain. Even
  // though the payload arrives via JSON.parse (which already treats those
  // keys as ordinary properties), the snapshot exposed on
  // `window.shinyreact._restore["-values"]` is constructed from untrusted
  // input ids — defend in depth at the assignment site as well.
  const applied = Object.create(null) as Record<string, unknown>;
  if (restore && typeof restore === "object") {
    for (const [id, value] of Object.entries(restore)) {
      registry.add(id, value);
      applied[id] = value;
    }
  }
  ns._restore = { "-applied": true, "-values": applied };
}
