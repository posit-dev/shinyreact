# shinyreact: posit::conf 2026 Goals

**Headline:** "An AI-first approach to writing Shiny apps"

**Target date:** posit::conf, September 2026
**Planning date:** April 6, 2026
**Primary developer:** Barret
**Testing support:** Karan

---

## Vision

Shiny has always been there to help R data scientists expose their work to decision makers without the need to be a full stack engineer. Claude is that engineer now. With Claude, we can write our UI using artificial intelligence, relieving you — the app author — from being an implementation engineer, letting you reclaim your time spent debugging Shiny.

`shinyreact` is the infrastructure that makes this possible.

**Key insights:**

1. **Shiny's promise, revisited.** Shiny removed the need for data scientists to become web developers. `shinyreact` removes the next barrier — the need to become a *Shiny* developer. The app author describes what they want; the AI handles implementation details like HTMLDependencies, React components, JavaScript, and wiring.

2. **The AI is the full-stack engineer.** Claude can write a React component, register it with `shinyreact`, and integrate the HTMLDependency in one shot. Normal users never wrote these things — and now they truly don't have to. The AI *is* the build step.

3. **The UI generation process is invisible.** The app author doesn't care how the UI gets built — HTMLDependencies, React components, JSON specs, output bindings — none of that matters to them. It's an implementation detail. What matters is the result: a working app that looks good and does what they asked for. The part you need to know and trust — the server logic, the data pipeline, the reactive graph — is in the language you're comfortable with: R or Python.

4. **Reclaim your time.** Data scientists spend too much time debugging Shiny layout, CSS, and JS interop instead of doing data science. With an AI-first approach, the implementation burden shifts from the human to the agent. You describe the app; Claude builds it.

5. **Design systems become accessible.** Companies can build their own component libraries (like `shinyshadcn`) on top of `shinyreact`. Claude picks from these libraries to produce high-quality, consistent apps — matching your organization's look and feel without you learning a design framework.

By posit::conf, the story is: *Tell Claude what you want your Shiny app to do. Claude writes the Python (or R) app, writes any needed React components, wires up the HTMLDependencies, and you have a working modern UI — without ever touching JS yourself.*

## Must-haves by September

### 1. shinyreact core is stable and documented

The plumbing just works. Downstream packages can build on it confidently.

- Stable API surface for JS hooks and the Python/R public API
- Clear documentation and examples
- **Feature/benefit catalog** — comprehensive nested bullet list of every feature and benefit for documentation source-of-truth.

Remaining known issues are tracked in the [GitHub issue tracker](https://github.com/posit-dev/shinyreact/issues).

### 2. Migrate Shiny JavaScript to its own repo

The vendored `shiny-react` code at `js/src/shiny-react/` and the broader Shiny JS infrastructure should live in its own repository, independent of `shinyreact`. This enables:

- Other packages (not just `shinyreact`) to depend on shiny-react
- Independent versioning and release cycle
- Cleaner separation of concerns between Shiny's JS plumbing and `shinyreact`'s rendering

### 3. shinyshadcn (or equivalent) exists as a proof-of-concept

`shinyshadcn` is a *reference implementation* — it shows the pattern works with a real design system. It is not the only option. Companies/groups could implement their own component library on top of `shinyreact` using their own design system for high-quality, consistent apps.

- Demonstrates the downstream package pattern end-to-end
- Shows that a standalone JS component library consuming `window.shinyreact` works in practice (Tenet 8 in `DESIGN.md`)
- Provides a meaningful set of components for demo purposes

### 4. Claude can reliably generate shinyreact apps

The API surface is AI-friendly. This has three dimensions:

- **(A) Documentation & context:** Good CLAUDE.md, docs, and examples so that Claude Code already works well with `shinyreact` — the API is AI-friendly by design
- **(B) Tooling:** Specific tooling — e.g., a skill, MCP server, or prompt templates that help Claude scaffold `shinyreact` apps
- **(C) API simplicity:** The API surface itself is simplified/refined so there's less for Claude to get wrong

**100 examples by conf.** The example gallery should grow to 100 — a comprehensive showcase of what `shinyreact` can do. This serves double duty: it proves the framework handles real-world use cases, and it gives Claude a rich training set to draw from when generating apps. Many of these examples should themselves be AI-generated, dogfooding the "AI-first" story.

### 5. Architecture article: "Where is Shiny useful?"

A written piece that articulates where Shiny fits in the modern app landscape — what problems it solves, where it's the right tool vs. alternatives, and how the AI-first approach changes the calculus. Helps frame the posit::conf narrative and gives the community a reference to point to.

### 6. R package has feature parity with Python

Full feature parity — not just a demo, the real thing.

The R package ships `page_react_html()`, `reactive_output()`, `send_message()`, `page_bare()`, `page_react_dep()`, the `shinyreact.default` / `shinyreact.asis` input handlers, and bookmark restore — over the same JS bundle as Python (byte-identical). Remaining gaps are tracked in [#182](https://github.com/posit-dev/shinyreact/issues/182) (script attributes), [#183](https://github.com/posit-dev/shinyreact/issues/183) (bookmark JSON escaping), [#184](https://github.com/posit-dev/shinyreact/issues/184) (smaller API divergences), and [#185](https://github.com/posit-dev/shinyreact/issues/185) (test coverage).

## Nice-to-haves (can wait)

### No-build-step component authoring

Claude can define components without requiring npm/vite/bundling (as `examples/01-hello` and `examples/02-columns` already do). Also: the ability to point at any npm package / CDN resource and have `shinyreact` consume it at runtime without a build step. Compelling, but not required for the September narrative.

## Team allocation

- **Barret:** All development — shinyreact core, R package, shinyshadcn, AI tooling, documentation
- **Karan:** Testing support
