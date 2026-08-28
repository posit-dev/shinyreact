---
name: shinyreact-convert-app
description: Convert an existing Shiny app (R or Python) to the shinyreact ui.tsx pattern — inspect the source, drive the running app in a browser, describe it in plain English, then port it against that description. Use when the user asks to port, convert, migrate, rewrite, or "React-ify" a Shiny app, or to reproduce an existing app's UI in React.
---

# Converting an existing Shiny app to shinyreact

The failure mode of this task is not writing bad React. It is **porting an app
you never understood** — reproducing the widgets you can see in the source
while silently dropping the behavior that only shows up when you use it: what
is disabled until something else is set, what updates live versus on submit,
what the empty state says, which control secretly drives two outputs.

So the order is fixed:

```
inspect the source  →  drive the running app  →  write PORT.md in plain English
                    →  implement against it   →  verify
```

Do not write a line of the new app before `PORT.md` exists. If the user asks
you to skip straight to code, port the smallest slice and write its `PORT.md`
section anyway — the description is what makes the port checkable by anyone
other than you.

Use the `shinyreact` skill for how to *write* the new app. This skill is about
knowing what to write.

## Phase 1 — inspect the source

Read the whole app before summarizing any of it. Build these inventories and
**count** each, because "I read the app" is not a claim anyone can check:

| Inventory | What to capture |
|---|---|
| Inputs | id, widget type, default, range/choices, and every place the server reads it |
| Outputs | id, renderer (`renderPlot`, `renderText`, `renderDT`, `render_plotly`, …), and the UI element that hosts it |
| Reactives | `reactive()` / `@reactive.calc` / `eventReactive` / `observeEvent` — who triggers what |
| Data | source, shape, grain, size, whether it is loaded once or per session |
| Layout | pages/tabs, sidebar, cards, and what is nested in what |
| Conditional UI | `conditionalPanel`, `req()`, `validate/need`, `update*Input`, `insertUI` |
| Modules | each module's namespace and its input/output surface |
| Non-Shiny deps | DT, plotly, leaflet, bslib themes, custom CSS/JS |

Two questions to answer explicitly, because they decide the port's shape:

- **What does each output actually contain?** A `renderPlot` that draws a chart
  from a small data frame becomes data + a client-side chart. A `renderPlot`
  of something matplotlib-specific stays server-rendered behind `ImageOutput`.
- **Where does the reactivity fan out?** One filter feeding six cards should
  become one shared `@reactive.calc` and six aggregations, not six independent
  pipelines.

## Phase 2 — drive the running app

Static reading cannot tell you what the app *feels* like. Run it and use it.

Ask the user how to start it if it is not obvious. Then, with the browser tools
(`claude-in-chrome`, or Playwright):

- Take a screenshot of the initial state before touching anything. That is the
  empty/default state, and it is the state ports most often get wrong.
- Move **every** control, including to its extremes and to an empty value.
  Note what re-renders, what does not, and what flashes.
- Watch for things no source read reveals: debounce (does it update while
  dragging or on release?), controls that disable each other, validation
  messages, an output that stays stale during recompute versus one that blanks.
- Note exact copy: labels, button text, placeholder text, empty-state strings,
  singular/plural. The port should be diffable against the original by reading.
- Check the console and network only if something looks wrong; do not go
  spelunking.

Keep this bounded. If the app needs credentials, data you do not have, or more
than a few minutes of clicking to reach a state, stop and ask the user rather
than exploring further.

## Phase 3 — write `PORT.md`

One file at the root of the new app. It has two parts, and both matter:

**Part 1 — the behavior tree.** What the app does, in plain English, one
atomically checkable claim per leaf. This is the same format as
`examples/*/FEATURES.md` in the shinyreact repo — read one of those first; they
are worked examples. The rules:

- Behavior, not implementation. "the caption reads `N eruptions in M bins`,
  singular `bin` at M=1", not "calls `format()`".
- Specifics or nothing. Exact ids, defaults, ranges, copy, wire shapes. "handles
  empty input" is unauditable.
- Mark uncertainty with `(verify)` rather than dropping it. A leaf you were not
  sure of and silently omitted is how a tree becomes untrustworthy.
- Present tense, describing the **original** app. This is the specification the
  port is judged against.

**Part 2 — checklists.** One checklist per feature area (per tab, per card, per
data path — whatever the app's own seams are), with a checkbox per leaf or
small group of leaves:

```markdown
## Checklist — filters sidebar

- [x] date range picker, defaults to the last 30 days
- [x] search box, debounced ~300 ms, matches name and id
- [ ] category multi-select, empty means "all"
- [ ] reset button clears all three and re-runs
```

Add a short **Status** line at the top (what is done, what is next, what is
blocked) and a **Deliberate divergences** section for anything you are *not*
porting as-is, with the reason. An unexplained difference reads as a bug
forever.

## Phase 4 — implement, updating `PORT.md` as you go

`PORT.md` is the shared progress record — other agents and the user read it to
know where the port stands, so a stale one is worse than none.

- Tick a box **when the behavior works**, not when the code is written.
- When you discover the description was wrong, fix the description in the same
  change, and say so in the Status line. The original app wins over your notes.
- When you decide not to port something, move it to Deliberate divergences
  rather than leaving the box unticked forever.
- Keep the file's structure stable between updates so a diff is readable.

Port order that avoids rework: data + reactives first (they decide the output
shapes), then one full vertical slice end to end (one input, one output,
rendered), then the rest of the outputs, then layout and polish.

## Phase 5 — verify

Read `.claude/references/verifying-ui-code.md` before writing tests. In short:
factor pure logic out of the app file so it is importable, test the client by
mounting the real `www/ui.js` against a fake Shiny, and reserve Playwright for
what those cannot reach.

Every leaf you assert gets a `(test)` marker in `PORT.md`. Finish by
re-driving the ported app in the browser against the checklists — including the
initial state screenshot from Phase 2, side by side.

## Translation table

| Original | shinyreact |
|---|---|
| `sliderInput` / `textInput` / `selectInput` | your own React control + `useShinyInput(id, default)` |
| `actionButton` | `useShinyInput(id, 0, {debounceMs: 0, priority: "event"})`, increment on click; `@reactive.event(..., ignore_init=True)` server-side |
| `renderText` / `renderPrint` | `reactive_output` returning the string, `useShinyOutputValue` client-side |
| `renderPlot` (data you could draw) | `reactive_output` returning the data; draw in React |
| `renderPlot` (matplotlib/ggplot-specific) | keep the renderer, host it with `ImageOutput` |
| `renderDT` / `render.data_frame` / `renderPlotly` | keep the renderer, host it with `ShinyOutput` — no `*Output()` placeholder needed |
| `conditionalPanel` | ordinary React conditional rendering; no server round trip |
| `update*Input` | the client already owns the value — set React state; use `send_message` only for genuine server-initiated events |
| `req()` / `validate` | return `None` / `NULL` and let the client show its empty state |
| Shiny modules | `ShinyModuleProvider` around the subtree |
| `insertUI` / `removeUI` | React state, not DOM surgery |

Two things worth deciding early rather than discovering late: the app's
**layout system** (Tailwind + shadcn/ui if it needs a component library, plain
CSS if not — a `package.json` is a permanent cost) and whether any output must
stay server-rendered, because that decides whether the port needs
`ImageOutput` / `ShinyOutput` at all.
