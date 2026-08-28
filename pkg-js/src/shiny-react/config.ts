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
 * Show a handshake failure on the page, then throw it.
 *
 * The throw alone leaves a blank page whose only explanation is in DevTools —
 * the handshake fails during the first hook mount, before anything renders.
 * The banner is plain DOM on purpose: the failure being reported is precisely
 * "the bundle and the server cannot talk to each other", so the surface must
 * not depend on Shiny being alive. Idempotent by element id.
 *
 * `message` may mark literals (versions, ids, package names) with backticks;
 * they render as `<code>` chips on the page and are stripped from the thrown
 * Error, whose consumer is a console. Text is set via `textContent`, never
 * `innerHTML` — a server-supplied version string must not be able to inject
 * markup.
 *
 * Colors are WCAG AA at minimum: #7f1d1d on #fee2e2 is ~9.5:1, and the chips
 * are ~11:1 on white. The banner never relies on color alone — it carries the
 * full sentence and `role="alert"`.
 */
export function throwVisibly(message: string): never {
  if (typeof document !== "undefined" && document.body) {
    const id = "shinyreact-fatal-error";
    let existing = document.getElementById(id);
    if (!existing) {
      existing = document.createElement("div");
      existing.id = id;
      existing.setAttribute("role", "alert");
      existing.style.cssText =
        "position:fixed;top:0;left:0;right:0;z-index:99999;padding:1rem 1.25rem;" +
        "background:#fee2e2;color:#7f1d1d;border-bottom:4px solid #991b1b;" +
        "font-family:system-ui,sans-serif;font-size:15px;line-height:1.5;" +
        "white-space:pre-wrap";
      document.body.appendChild(existing);
    }
    const el = existing;
    el.textContent = "";
    // Odd segments were inside backticks.
    message.split("`").forEach((segment, i) => {
      if (i % 2 === 0) {
        el.appendChild(document.createTextNode(segment));
        return;
      }
      const code = document.createElement("code");
      code.textContent = segment;
      code.style.cssText =
        "background:#fff;color:#7f1d1d;border:1px solid #f0a3a3;border-radius:4px;" +
        "padding:0.1em 0.35em;font-family:ui-monospace,SFMono-Regular,monospace;" +
        "font-size:0.95em";
      el.appendChild(code);
    });
  }
  throw new Error(message.replace(/`/g, ""));
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
    throwVisibly(
      `shinyreact protocol mismatch: the server speaks protocol ` +
        `\`${serverVersion}\` but this JS client supports ` +
        `\`${PROTOCOL_VERSION}\`. ` +
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
