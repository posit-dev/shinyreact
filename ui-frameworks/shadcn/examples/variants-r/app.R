# Variants gallery — every component and its variants/sizes laid out in rows.
#
# A visual reference sheet: each row shows one component across all its variants,
# sizes, or states, plus a couple of className customizations (changed colors/size).
# Run: shiny::runApp("ui-frameworks/shadcn/examples/variants-r")

library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
source(file.path(app_dir, "../../pkg-r/shadcn.R"))
dep <- shadcn_dep(file.path(app_dir, "../../www"))

ui <- page_react(
  tags$div(
    output_react("variants", extra_deps = list(dep)),
    style = "max-width:760px; margin:2.5rem auto; padding:0 1rem;"
  ),
  title = "shadcn x shinyreact — variants"
)

# A labeled row: caption above, variations wrapping below.
row <- function(label, ...) {
  tags$div(
    tags$div(label, class = "text-sm font-medium"),
    tags$div(..., class = "flex flex-wrap gap-2 items-center"),
    class = "flex flex-col gap-2"
  )
}

section <- function(...) tags$div(..., class = "flex flex-col gap-4")

server <- function(input, output, session) {
  output$variants <- render_react({
    shadcn_card(
      tags$div(
        tags$div("Variants & sizes", class = "text-lg font-semibold"),
        tags$div(
          "Every component across its variants, sizes, and states.",
          class = "text-sm text-muted-foreground"
        ),
        class = "flex flex-col gap-1"
      ),
      section(
        row(
          "Button · variants",
          shadcn_button("b_default", "Default"),
          shadcn_button("b_secondary", "Secondary", variant = "secondary"),
          shadcn_button("b_destructive", "Destructive", variant = "destructive"),
          shadcn_button("b_outline", "Outline", variant = "outline"),
          shadcn_button("b_ghost", "Ghost", variant = "ghost"),
          shadcn_button("b_link", "Link", variant = "link")
        ),
        row(
          "Button · sizes",
          shadcn_button("s_sm", "Small", size = "sm"),
          shadcn_button("s_default", "Default", size = "default"),
          shadcn_button("s_lg", "Large", size = "lg")
        ),
        row(
          "Button · custom (className)",
          shadcn_button("c_color", "Custom color", class = "bg-sky-600 hover:bg-sky-700"),
          shadcn_button("c_round", "Pill", variant = "outline", class = "rounded-full")
        )
      ),
      shadcn_separator(),
      row(
        "Badge · variants",
        shadcn_badge("default"),
        shadcn_badge("secondary", variant = "secondary"),
        shadcn_badge("destructive", variant = "destructive"),
        shadcn_badge("outline", variant = "outline"),
        shadcn_badge("ghost", variant = "ghost"),
        shadcn_badge("link", variant = "link"),
        shadcn_badge("custom", class = "bg-emerald-600 text-white")
      ),
      shadcn_separator(),
      row(
        "Switch · states",
        shadcn_switch("sw_off", label = "Off"),
        shadcn_switch("sw_on", label = "On", checked = TRUE)
      ),
      row(
        "Checkbox · states",
        shadcn_checkbox("cb_off", label = "Unchecked"),
        shadcn_checkbox("cb_on", label = "Checked", checked = TRUE)
      ),
      shadcn_separator(),
      tags$div(
        tags$div("Alert · variants", class = "text-sm font-medium"),
        shadcn_alert("A neutral, informational message.", title = "Heads up"),
        shadcn_alert("Something needs your attention.",
          title = "Error", variant = "destructive"
        ),
        class = "flex flex-col gap-2"
      ),
      title = "Component variants"
    )
  })
}

shinyApp(ui, server)
