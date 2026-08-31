/* eslint-disable @typescript-eslint/no-explicit-any */
import { type InputRegistry } from "./input-registry";
import {
  assertProtocolCompatible,
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

  // The protocol handshake runs BEFORE the already-applied check. It is a
  // property of the page, not of the restore payload, so a second call — or a
  // pre-set/forged `_restore` sentinel — must not be able to skip it. Doing the
  // early return first turned that sentinel into a silent kill switch for
  // version checking.
  // A missing tag is not an error in either build: a hand-wired
  // `page_bare(page_react_dep())` page legitimately has none, and there is
  // nothing to check when the server serves no client (#261).
  const config = readShinyReactConfig();
  if (config?.protocolVersion) {
    assertProtocolCompatible(config.protocolVersion);
  } else if (config != null) {
    // A config tag with no `protocolVersion` is not a page we emit: both
    // servers always include it. Previously this silently skipped version
    // checking altogether, which is the one thing the tag exists to prevent.
    console.error(
      "shinyreact: the #shinyreact-config tag carries no protocolVersion, so " +
        "the client cannot verify it speaks the same protocol as the server. " +
        "Upgrade the shinyreact Python/R package.",
    );
  }

  // Already applied — preserve the existing snapshot.
  if (existing && typeof existing === "object" && existing["-applied"]) {
    return;
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
