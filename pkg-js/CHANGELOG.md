# Changelog

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
