import { type InputRegistry } from "./input-registry";
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
export declare function applyRestoredValues(registry: InputRegistry): void;
