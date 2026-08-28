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

Use the `shinyreact-build-app` skill for how to *write* the new app. This skill is about
knowing what to write.

**This skill covers Python and R together** — both as the source you are
porting from and as the target. Anything unmarked holds in both; `[py]` and
`[r]` mark the few places they differ. The port does not have to stay in the
source app's language, and the client half is identical either way.

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

**Part 1 — the behavior tree.** What the app does, in plain English, as a
nested bullet list, one atomically checkable claim per leaf. The tree path says
*where* the claim lives (data vs. UI vs. reactivity vs. wire); the leaf says
*what to check*:

```
- histogram of Old Faithful eruption WAITING times
  - data: faithful.csv, column `waiting` (minutes, ~43-96)
    - NOT the `eruptions` column
  - binning matches R's hist(): equal-width, (lo, hi], first bin inclusive
- bins slider
  - range 1-50, default 9
  - updates live, not debounced
  - drives BOTH outputs
    - dist_data: {breaks: number[], counts: number[]}
    - dist_caption: "272 eruptions in N bins", singular "bin" when N=1
- while recalculating: previous chart stays mounted, dims (no skeleton flash)
```

The rules:

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

Three layers, cheapest first: factor pure logic out of the app file so it is
importable and test it directly; test the client by evaluating the real
`www/ui.js` against a fake `window.Shiny` in jsdom (not by importing the
component — that tests a copy the app does not ship); and reserve Playwright
for layout and real bindings, which the other two structurally cannot see. The
`shinyreact-build-app` skill's `references/testing.md` has the traps.

A port has one advantage a new app does not: **the original still runs.** Where
the logic is a pure transform, capture its output from the original app and
assert the same values in the port.

Every leaf you assert gets a `(test)` marker in `PORT.md`. Finish by
re-driving the ported app in the browser against the checklists — including the
initial state screenshot from Phase 2, side by side.

## Translation table

| Original | shinyreact |
|---|---|
| `sliderInput` / `textInput` / `selectInput` | a library control (shadcn/ui `Slider`, `Input`, `Select`) + `useShinyInput(id, default)` |
| `dateRangeInput` / `selectizeInput` | a real library component — a date picker or combobox, with `react-day-picker` / shadcn's `Combobox` underneath. Never hand-roll these |
| `actionButton` | `useShinyInput(id, 0, {debounceMs: 0, priority: "event"})`, increment on click; ignore the initial 0 server-side (`[py]` `@reactive.event(..., ignore_init=True)`, `[r]` an explicit `if (is.null(x) \|\| x == 0) return(NULL)`) |
| `renderText` / `renderPrint` | `reactive_output` returning the string, `useShinyOutputValue` client-side |
| `renderPlot` (data you could draw) | `reactive_output` returning the data; draw in React |
| `renderPlot` (matplotlib/ggplot-specific) | keep the renderer, host it with `ImageOutput` |
| `renderDT` / `render.data_frame` / `renderPlotly` | keep the renderer, host it with `ShinyOutput` — no `*Output()` placeholder needed, and its binding JS is discovered for you in both languages |
| `downloadButton` + `downloadHandler` | keep the `downloadHandler` unchanged — it is a server route, not a rendered value, and it works with no `downloadButton()` in any UI; host `<a class="shiny-download-link">` via `ShinyOutput` and Shiny's own binding fills in `href`. Never rebuild the file client-side from the JSON another output uses: the serializers disagree on details (R's `write.csv` renders `0.0002` as `2e-04`; a JS re-implementation will not) |
| `fileInput` | host a native `<input type="file">` (plus its label/button markup) via `ShinyOutput` so Shiny's own file-input binding does the multipart upload. Raw bytes cannot travel through `useShinyInput`, and reimplementing the upload RPC means depending on internal Shiny API |
| `tabsetPanel` / `navset_*` | a client-side tab strip that keeps every panel **mounted** and hides inactive ones (CSS `hidden`; Radix `Tabs` needs `forceMount`). Unmounting a panel drops its outputs' subscriptions mid-session (`Output not found` in the console); there is no suspend-when-hidden in this pattern, so note the always-computes divergence in `PORT.md` |
| `htmlTemplate("www/index.html")` / an app that owns `index.html` | keep the document and serve it with `page_react_html()` — see the next section |
| `conditionalPanel` | ordinary React conditional rendering; no server round trip |
| `update*Input` | the client already owns the value — set React state; use `send_message` only for genuine server-initiated events |
| `req()` / `validate` | return `None` / `NULL` and let the client show its empty state |
| Shiny modules | `ShinyModuleProvider` around the subtree |
| `insertUI` / `removeUI` | React state, not DOM surgery |

### Porting an app that owns its HTML document

When the source UI is `htmlTemplate("www/index.html")` (or `[py]` a
hand-written `index.html`), the document is part of the app's surface — port
the document, don't flatten it into `page_react()`:

- **Upgrade the head.** Delete the hardcoded Shiny includes old templates
  carry (`shared/jquery.min.js`, `shared/shiny.min.js`, `shiny.css`) and put
  the `{{ headContent() }}` marker inside `<head>` — spelled exactly like
  that, spaces included ([r] the check is a fixed-string match). Shiny's and
  shinyreact's tags render at the marker.
- **Serve it.** `[r]` `shinyApp(ui = page_react_html("www/index.html"), server)`;
  `[py]` `ReactApp(server)` discovers `www/index.html` on its own.
- The document keeps what the app owns (meta tags, fonts, analytics, the
  layout shell); the parts with *behavior* move into the React client as
  usual.
- `[r]` the whole file is an `htmlTemplate()`: every `{{ ... }}` in it
  evaluates as R, so escape Mustache/Vue-style braces the document may
  already contain.

Fall back to `page_react()` only when the document carries nothing worth
keeping — default scaffolding with no custom head content — and record that
in `PORT.md`'s Deliberate divergences, because silently dropping a file the
original ships reads as an omission.

### Startup ordering is not the original's

In the original app every input value exists synchronously at session start.
In the port each `useShinyInput` arrives on its own async round trip after
mount, so:

- An `eventReactive(..., ignoreNULL = FALSE)` / `@reactive.event(...,
  ignore_init=False)` can fire with sibling inputs still `NULL`.
- An event input with `debounceMs: 0` can outrun inputs left on the 100 ms
  default — the click counter's initial `0` reaches the server before the
  values the handler reads.

Give every input the handler reads at event time (via `isolate()` or inside
the event) `debounceMs: 0` as well, and guard the first flush with an explicit
`NULL`-or-initial-`0` check rather than trusting `ignoreInit` /
`ignore_init` alone — shinyreact's init ping flushes the reactive graph once
before real values arrive, which can spend that exemption.

### Two decisions to make before you start porting

**Which widgets you are not going to write.** Shiny's inputs look small in the
source and are not: `dateRangeInput` is a calendar with keyboard navigation and
range validation, `selectizeInput` is a searchable multi-select. A port that
re-implements them by hand is where the schedule goes, and it is code with no
upstream tests that the user now owns. Take shadcn/ui + Tailwind as the default
component layer, `@tanstack/react-table` for tables, `recharts` for ordinary
charts, `react-hook-form` + `zod` for form validation, `date-fns` for dates.

Write from scratch only what is specific to *this* app — its dashboard layout,
its one bespoke visualization.

**Which outputs stay server-rendered.** Decide per output, because it decides
whether the port needs `ImageOutput` / `ShinyOutput` at all. A `renderPlot` of
a small data frame becomes data plus a React chart. A ggplot with custom
annotations, or an existing DT/plotly/leaflet widget, stays where it is and
gets hosted — re-implementing a widget that already works is work you can
simply not do.
