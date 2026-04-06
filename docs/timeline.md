# shinyjson: posit::conf 2026 Goals

**Headline:** "An AI-first approach to writing Shiny apps"

**Target date:** posit::conf, September 2026
**Planning date:** April 6, 2026
**Primary developer:** Barret
**Testing support:** Karan

---

## Vision

Shiny has always been there to help R data scientists expose their work to decision makers without the need to be a full stack engineer. Claude is that engineer now. With Claude, we can write our UI using artificial intelligence, relieving you — the app author — from being an implementation engineer, letting you reclaim your time spent debugging Shiny.

shinyjson is the infrastructure that makes this possible.

**Key insights:**

1. **Shiny's promise, revisited.** Shiny removed the need for data scientists to become web developers. shinyjson removes the next barrier — the need to become a *Shiny* developer. The app author describes what they want; the AI handles implementation details like HTMLDependencies, React components, JavaScript, and wiring.

2. **The AI is the full-stack engineer.** Claude can write a React component, register it with shinyjson, and integrate the HTMLDependency in one shot. Normal users never wrote these things — and now they truly don't have to. The AI *is* the build step.

3. **The UI generation process is invisible.** The app author doesn't care how the UI gets built — HTMLDependencies, React components, JSON specs, output bindings — none of that matters to them. It's an implementation detail. What matters is the result: a working app that looks good and does what they asked for. The part you need to know and trust — the server logic, the data pipeline, the reactive graph — is in the language you're comfortable with: R or Python.

4. **Reclaim your time.** Data scientists spend too much time debugging Shiny layout, CSS, and JS interop instead of doing data science. With an AI-first approach, the implementation burden shifts from the human to the agent. You describe the app; Claude builds it.

5. **Design systems become accessible.** Companies can build their own component libraries (like shinyshadcn) on top of shinyjson. Claude picks from these libraries to produce high-quality, consistent apps — matching your organization's look and feel without you learning a design framework.

By posit::conf, the story is: *Tell Claude what you want your Shiny app to do. Claude writes the Python (or R) app, writes any needed React components, wires up the HTMLDependencies, and you have a working modern UI — without ever touching JS yourself.*

## Must-haves by September

### 1. shinyjson core is stable and documented

The plumbing just works. Downstream packages can build on it confidently.

- Stable API surface for JS hooks and Python public API
- Clear documentation and examples
- Known issues resolved:
  - **Duplicate output IDs on tab navigation** — switching tabs unmounts/remounts useShinyOutput components, creating duplicate bindings. Fix output registry cleanup/re-registration or keep pages mounted.
  - **Python-side input handlers** — useShinyInput values arrive raw with no server-side interception. Need to support registering Python input handlers for validation/transformation (like Shiny's built-in action button handler).
  - **XSS in chat example** — renderMarkdown passes non-code-block text as raw HTML via dangerouslySetInnerHTML. Needs sanitization (DOMPurify or React element tree).
  - **Component contract definition** — define what a well-formed shinyjson component looks like from a downstream author's perspective (props, composition, catalog conventions).
  - **Render method surface area** — evaluate which render patterns are most valuable (single element without full Spec, streaming partial updates, HTML fragments, component lists).
  - **Dynamic UI support** — can render output include arbitrary Shiny UI (ui.tags, ui.input_slider) mixed with shinyjson components, or must it always be component trees?
  - **Full React page support** — remaining work for `page_react()` layout, graceful late-Shiny-arrival for all hooks, example app.
  - **Feature/benefit catalog** — comprehensive nested bullet list of every feature and benefit for documentation source-of-truth.

### 5. Migrate Shiny JavaScript to its own repo

The vendored `shiny-react` code at `js/src/shiny-react/` and the broader Shiny JS infrastructure should live in its own repository, independent of shinyjson. This enables:

- Other packages (not just shinyjson) to depend on shiny-react
- Independent versioning and release cycle
- Cleaner separation of concerns between Shiny's JS plumbing and shinyjson's JSON rendering

### 2. shinyshadcn (or equivalent) exists as a proof-of-concept

shinyshadcn is a *reference implementation* — it shows the pattern works with a real design system. It is not the only option. Companies/groups could implement their own component library on top of shinyjson using their own design system for high-quality, consistent apps.

- Demonstrates the downstream package pattern end-to-end
- Shows that the extension mechanism (registerComponents, render subclass, extra_deps) works in practice
- Provides a meaningful set of components for demo purposes

### 3. Claude can reliably generate shinyjson apps

The API surface is AI-friendly. This has three dimensions:

- **(A) Documentation & context:** Good CLAUDE.md, docs, and examples so that Claude Code already works well with shinyjson — the API is AI-friendly by design
- **(B) Tooling:** Specific tooling — e.g., a skill, MCP server, or prompt templates that help Claude scaffold shinyjson apps
- **(C) API simplicity:** The API surface itself is simplified/refined so there's less for Claude to get wrong

**100 examples by conf.** The example gallery should grow from 9 to 100 — a comprehensive showcase of what shinyjson can do. This serves double duty: it proves the framework handles real-world use cases, and it gives Claude a rich training set to draw from when generating apps. Many of these examples should themselves be AI-generated, dogfooding the "AI-first" story.

### 6. Architecture article: "Where is Shiny useful?"

A written piece that articulates where Shiny fits in the modern app landscape — what problems it solves, where it's the right tool vs. alternatives, and how the AI-first approach changes the calculus. Helps frame the posit::conf narrative and gives the community a reference to point to.

### 4. R package has feature parity with Python

Full feature parity — not just a demo, the real thing:

- `shinyjson::ui()` — equivalent to Python's `shinyjson.ui()`
- `shinyjson::render` — equivalent to `@shinyjson.render`
- `Spec` / `Element` data model
- `post_message()` support
- Same extension pattern works for R downstream packages

## Nice-to-haves (can wait)

### No-build-step component authoring

Claude can define + register components without requiring npm/vite/bundling. Also: the ability to point at any npm package / CDN resource and have shinyjson consume it at runtime without a build step. Compelling, but not required for the September narrative.

### JSON Patch for partial updates

RFC 6902 JSON Patch operations to send incremental spec updates from Python instead of full spec replacement. Valuable for large specs and streaming/AI-generated UIs, but not needed for the core story.

### Build step for example JS

Examples currently use `React.createElement` directly (no JSX). A lightweight build step (esbuild with JSX) would improve readability. Low priority — examples work as-is.

### Chat example mock mode

7-chat requires OPENAI_API_KEY. An echo/mock mode would enable smoke-testing without credentials.

## Current state (April 2026)

- **JS core:** Working — hooks (useShinyInput, useShinyOutput, useShinyMessageHandler, useShinyInitialized), registerComponents, output binding all functional
- **Python package:** Working — ui(), render, Spec/Element, post_message all functional
- **R package:** Placeholder — not yet implemented
- **Examples:** 9 examples (hello-world through blended), most working — target is 100 by conf
- **Known issues:** Duplicate output IDs on tab nav, chat example needs API key, no input handlers, XSS in chat markdown, component contract undefined, render method surface area unexplored

## Gap analysis

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| shinyjson JS core | Working, some known bugs | Stable, bugs fixed | Medium — duplicate output IDs, component contract, dynamic UI, full React page |
| shinyjson Python | Working | Stable, documented | Medium — input handlers, render surface area, docs |
| shinyjson R | Placeholder | Feature parity with Python | **Large** — full implementation needed |
| shiny-react repo | Vendored in js/src/shiny-react/ | Own repo, independently versioned | **Medium** — extract, set up repo/CI, update consumers |
| shinyshadcn | Exists as example (5-shadcn) | Real downstream package | Medium — extract into standalone package |
| AI integration | CLAUDE.md exists | Docs + tooling + simplified API | Medium — skill/MCP server, API refinement |
| Documentation | README + CLAUDE.md | Comprehensive user-facing docs | Medium — feature catalog, user guides |
| Security | XSS in chat markdown | Sanitized rendering | Small — add DOMPurify or React element tree |

## Team allocation

- **Barret:** All development — shinyjson core, R package, shinyshadcn, AI tooling, documentation
- **Karan:** Testing support
