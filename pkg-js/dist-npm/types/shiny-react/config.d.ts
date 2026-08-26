/**
 * The wire-protocol version this client speaks.
 *
 * The server (shinyreact for R/Python) renders its protocol version into the
 * page via the `#shinyreact-config` JSON script tag; the client asserts the
 * major versions match at boot. The protocol covers the shapes that cross the
 * client/server boundary — the `#shinyreact-config` payload itself, the
 * `shinyReactMessage` custom message, and the `shinyreact.default` /
 * `shinyreact.asis` input-handler contract — and only bumps when one of those
 * changes, so client and server package releases do not need to be in
 * lockstep. Decided in decisions/2026-08-17-js-distribution.md.
 */
export declare const PROTOCOL_VERSION = "1.0";
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
export declare function readShinyReactConfig(): ShinyReactConfig | null;
/**
 * Fail fast when the server's protocol major version disagrees with this
 * client's. Same-major means compatible; a mismatch means one side must be
 * upgraded, and silently continuing would surface as undebuggable payload
 * corruption instead of this message.
 */
export declare function assertProtocolCompatible(serverVersion: string): void;
/** Opt into treating a missing `#shinyreact-config` tag as a hard error. */
export declare function requireShinyReactConfigTag(): void;
export declare function isShinyReactConfigTagRequired(): boolean;
/** Test-only: undo requireShinyReactConfigTag(). */
export declare function _resetConfigTagRequirementForTesting(): void;
