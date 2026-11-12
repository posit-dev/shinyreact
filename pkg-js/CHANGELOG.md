# Changelog

## Unreleased

- `useShinyOutputValue()` and its sibling hooks no longer leak a Shiny output
  binding each time a component unmounts. Before, every mount/unmount cycle
  (e.g. switching tabs) added a stale binding, so Shiny's "Duplicate output
  IDs were found" warning grew and the console logged `Output <id> not found`
  (#330).

- New `useShinyConnected()` hook: `false` once the session disconnects, `true`
  again if Shiny reconnects (#328).

- `useShinyBusy()` now updates in a real browser. Shiny fires `shiny:busy` /
  `shiny:idle` through jQuery, which never reached the hook's
  `addEventListener()` listeners (#328).

- Renderer dependency discovery now installs when Shiny loads after the
  bundle. It waited for `shiny:connected` with a native listener, which the
  jQuery-fired event never reached (#328).

- `ImageOutput` hides the last image and shows the error message when the
  render function errors, with Shiny's `shiny-output-error` classes. Its
  `<img>` now uses the renderer's `alt` text instead of `alt=""` (#327).

- `useShinyOutputValue()` is now typed `T | null | undefined`. A server
  `NULL` / `None` arrives as `null`, which the old `T | undefined` type hid.
  Passing a `defaultValue` narrows it to `T | null` (#329).

- The stylesheet is also exported as `@posit-dev/shinyreact/styles.css`, so
  TypeScript resolves the import with no `declare module` (#329).

## 0.1.1

- First release published through CI with npm trusted publishing
  (staged, human-approved). Same code as 0.1.0 plus a README for npm.

## 0.1.0

- Initial npm release as `@posit-dev/shinyreact`. Published by hand to
  bootstrap the package; no `js/v0.1.0` tag.

- ESM entry for bundler-tier apps with React externalized as a peer
  dependency, plus type declarations and `@posit-dev/shinyreact/styles`.

- Hooks: `useShinyInput`, `useShinyInputValue`, `useSetShinyInput`,
  `useShinyOutputValue`, `useShinyOutputStatus`, `useShinyOutputError`,
  `useShinyMessageHandler`, `useShinyInitialized`, `useShinyBusy`.

- Components and utilities: `ShinyOutput`, `ImageOutput`,
  `ShinyModuleProvider`, `MISSING`.

- Asserts the wire-protocol major version against the server's
  `#shinyreact-config` tag at boot, and warns when a page also serves the IIFE
  bundle alongside this package.
