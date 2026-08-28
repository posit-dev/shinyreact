/**
 * The wire-protocol version this client speaks.
 *
 * The server (shinyreact for R/Python) renders its protocol version into the
 * page via the `#shinyreact-config` JSON script tag; the client asserts the
 * major versions match at boot. The protocol covers every shape that crosses
 * the client/server boundary; protocol/surface.json enumerates them and a test
 * in each language enforces it. Only changes an existing peer would
 * misinterpret bump this version — additive shapes do not (see
 * protocol/README.md) — so client and server package releases do not need to
 * be in lockstep. Decided in decisions/2026-08-17-js-distribution.md.
 */
export const PROTOCOL_VERSION = "1.0";

/** Payload of the `#shinyreact-config` script tag emitted by the server. */
export interface ShinyReactConfig {
  protocolVersion?: string;
  /** Bookmark-restored input values, present only when restoring. */
  restore?: Record<string, unknown>;
}

/**
 * Read and parse the `#shinyreact-config` JSON script tag, or return null
 * when the tag is absent (e.g. a server predating the tag, or a non-DOM
 * environment). A malformed payload logs and returns null rather than
 * throwing — a broken config should not take down an app that never
 * bookmarks.
 */
export function readShinyReactConfig(): ShinyReactConfig | null {
  if (typeof document === "undefined") return null;
  const el = document.getElementById("shinyreact-config");
  const text = el?.textContent;
  if (!text) return null;
  try {
    return JSON.parse(text) as ShinyReactConfig;
  } catch (err) {
    console.error("shinyreact: could not parse #shinyreact-config JSON", err);
    return null;
  }
}

/**
 * Fail fast when the server's protocol major version disagrees with this
 * client's. Same-major means compatible; a mismatch means one side must be
 * upgraded, and silently continuing would surface as undebuggable payload
 * corruption instead of this message.
 */
export function assertProtocolCompatible(serverVersion: string): void {
  const major = (v: string) => v.split(".")[0];
  if (major(serverVersion) !== major(PROTOCOL_VERSION)) {
    throw new Error(
      `shinyreact protocol mismatch: the server speaks protocol ` +
        `${serverVersion} but this JS client supports ${PROTOCOL_VERSION}. ` +
        `Upgrade the older side (the shinyreact R/Python package, or the ` +
        `client bundle) so the major protocol versions match.`,
    );
  }
}

// Whether a missing `#shinyreact-config` tag is an error. The IIFE bundle
// ships inside the server package and cannot skew, so it tolerates absence
// (hand-wired page_bare() pages legitimately lack the tag). The npm build is
// installed independently, so absence there means the server predates the
// protocol — its entry point opts into strictness at import time.
let configTagRequired = false;

/** Opt into treating a missing `#shinyreact-config` tag as a hard error. */
export function requireShinyReactConfigTag(): void {
  configTagRequired = true;
}

export function isShinyReactConfigTagRequired(): boolean {
  return configTagRequired;
}

/** Test-only: undo requireShinyReactConfigTag(). */
export function _resetConfigTagRequirementForTesting(): void {
  configTagRequired = false;
}
