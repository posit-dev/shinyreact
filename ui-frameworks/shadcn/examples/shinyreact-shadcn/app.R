# shadcn x shinyreact — Component Explorer
#
# All 47 components, every variant, fully interactive.
# Run: shiny::runApp("ui-frameworks/shadcn/examples/shinyreact-shadcn")

library(shiny)
library(shinyreact)

app_dir <- normalizePath(".")
pkgload::load_all(file.path(app_dir, "../../pkg-r"), quiet = TRUE)
dep <- shadcn_dep()

# The page-chrome wrapper (outside the React tree) is the ONLY place a string
# `style=` is safe — inside a render_react tree it throws React error #62.
ui <- page_react(
  tags$div(
    output_react("gallery", extra_deps = list(dep)),
    style = "max-width: 1120px; margin: 0 auto; padding: 2.5rem 1.25rem;"
  ),
  title = "shadcn x shinyreact — Component Explorer"
)

# ── Helpers ──────────────────────────────────────────────────────────────────

# One variant preview card.
v <- function(label, ..., wide = FALSE) {
  extra <- if (wide) " col-span-2" else ""
  tags$div(
    tags$div(
      label,
      class = paste(
        "text-xs font-medium text-muted-foreground uppercase",
        "tracking-wide mb-3"
      )
    ),
    tags$div(..., class = "flex items-start gap-2 flex-wrap w-full"),
    class = paste0("rounded-lg border bg-card p-5 flex flex-col", extra)
  )
}

# Component section: heading + description + variant grid.
sec <- function(name, badge, subtitle, ...) {
  tags$div(
    tags$div(
      tags$div(
        tags$h2(name, class = "text-2xl font-semibold tracking-tight"),
        shadcn_badge(badge, variant = "secondary"),
        class = "flex items-center gap-3"
      ),
      tags$div(subtitle, class = "text-sm text-muted-foreground mt-1"),
      class = "pb-4 border-b mb-6"
    ),
    tags$div(..., class = "grid grid-cols-2 gap-4 mb-16")
  )
}

# ── Inputs ───────────────────────────────────────────────────────────────────

sec_button <- function() {
  sec(
    "Button",
    "Action",
    "Triggers server events. Six variants, three sizes, click counter via input.",
    v("Default", shadcn_button("btn_default", "Click me")),
    v(
      "Secondary",
      shadcn_button("btn_sec", "Secondary", variant = "secondary")
    ),
    v(
      "Destructive",
      shadcn_button("btn_del", "Delete", variant = "destructive")
    ),
    v("Outline", shadcn_button("btn_out", "Outline", variant = "outline")),
    v("Ghost", shadcn_button("btn_ghost", "Ghost", variant = "ghost")),
    v(
      "Sizes",
      tags$div(
        shadcn_button("btn_sm", "Small", size = "sm"),
        shadcn_button("btn_md", "Default"),
        shadcn_button("btn_lg", "Large", size = "lg"),
        class = "flex gap-2 items-center flex-wrap"
      )
    )
  )
}

sec_text_input <- function() {
  sec(
    "Text Input",
    "Input",
    "Single-line text field. Server reads input as a string; debounced by default.",
    v("Bare", shadcn_input("ti_bare", placeholder = "Placeholder text…")),
    v(
      "With label",
      shadcn_input(
        "ti_label",
        label = "Full name",
        placeholder = "Enter your name…"
      )
    ),
    v(
      "No debounce (fires on every keystroke)",
      shadcn_input("ti_fast", placeholder = "Immediate…", debounce_ms = 0)
    )
  )
}

sec_textarea <- function() {
  sec(
    "Textarea",
    "Input",
    "Multi-line text input. Same wire format as text_input.",
    v("Bare", shadcn_textarea("ta_bare", placeholder = "Write something…")),
    v(
      "With label",
      shadcn_textarea(
        "ta_label",
        label = "Notes",
        placeholder = "Add notes here…"
      )
    )
  )
}

sec_select <- function() {
  sec(
    "Select",
    "Input",
    "Dropdown selector. Choices are strings or list(value, label).",
    v(
      "String list",
      shadcn_select("sel_str", list("Apple", "Banana", "Cherry", "Durian"))
    ),
    v(
      "With label + pre-selected",
      shadcn_select(
        "sel_lang",
        list(
          list(value = "r", label = "R"),
          list(value = "py", label = "Python"),
          list(value = "js", label = "JavaScript"),
          list(value = "ts", label = "TypeScript")
        ),
        label = "Language",
        selected = "py"
      )
    )
  )
}

sec_slider <- function() {
  sec(
    "Slider",
    "Input",
    "Numeric range slider. Server reads input as a number.",
    v(
      "Default (0–100)",
      shadcn_slider("sli_bare", min = 0, max = 100, value = 40)
    ),
    v(
      "With label",
      shadcn_slider(
        "sli_label",
        min = 0,
        max = 100,
        value = 65,
        label = "Volume"
      )
    ),
    v(
      "Fine steps (0.0–1.0)",
      shadcn_slider(
        "sli_fine",
        min = 0,
        max = 1,
        step = 0.05,
        value = 0.5,
        label = "Opacity"
      )
    )
  )
}

sec_checkbox <- function() {
  sec(
    "Checkbox",
    "Input",
    "Boolean checkbox. Server reads input as TRUE/FALSE.",
    v("Unchecked", shadcn_checkbox("chk_a", "Accept terms")),
    v(
      "Checked by default",
      shadcn_checkbox("chk_b", "Subscribe", checked = TRUE)
    ),
    v(
      "Multiple",
      tags$div(
        shadcn_checkbox("chk_c", "Email notifications"),
        shadcn_checkbox("chk_d", "Weekly digest", checked = TRUE),
        shadcn_checkbox("chk_e", "Marketing"),
        class = "flex flex-col gap-2"
      )
    )
  )
}

sec_switch <- function() {
  sec(
    "Switch",
    "Input",
    "Toggle switch. Server reads input as TRUE/FALSE.",
    v("Off by default", shadcn_switch("sw_off", label = "Airplane mode")),
    v(
      "On by default",
      shadcn_switch("sw_on", label = "Dark mode", checked = TRUE)
    ),
    v(
      "Multiple",
      tags$div(
        shadcn_switch("sw_a", label = "Wi-Fi", checked = TRUE),
        shadcn_switch("sw_b", label = "Bluetooth"),
        shadcn_switch("sw_c", label = "NFC", checked = TRUE),
        class = "flex flex-col gap-3"
      )
    )
  )
}

sec_radio_group <- function() {
  sec(
    "Radio Group",
    "Input",
    "Single-select from a list. Server reads input as the selected string.",
    v(
      "String choices",
      shadcn_radio_group(
        "rg_str",
        list("Comfortable", "Compact", "Spacious"),
        selected = "Comfortable"
      )
    ),
    v(
      "Dict choices + label",
      shadcn_radio_group(
        "rg_theme",
        list(
          list(value = "light", label = "Light"),
          list(value = "dark", label = "Dark"),
          list(value = "system", label = "System")
        ),
        label = "Theme",
        selected = "system"
      )
    )
  )
}

sec_toggle <- function() {
  sec(
    "Toggle",
    "Input",
    "Two-state toggle button. Server reads input as TRUE/FALSE.",
    v(
      "Default variant",
      tags$div(
        shadcn_toggle("tog_a", "Bold"),
        shadcn_toggle("tog_b", "Italic", pressed = TRUE),
        class = "flex gap-2"
      )
    ),
    v(
      "Outline variant",
      tags$div(
        shadcn_toggle("tog_c", "Outline", variant = "outline"),
        shadcn_toggle("tog_d", "Pressed", variant = "outline", pressed = TRUE),
        class = "flex gap-2"
      )
    ),
    v(
      "Sizes",
      tags$div(
        shadcn_toggle("tog_sm", "Sm", size = "sm"),
        shadcn_toggle("tog_md", "Default"),
        shadcn_toggle("tog_lg", "Lg", size = "lg"),
        class = "flex gap-2 items-center"
      )
    )
  )
}

sec_toggle_group <- function() {
  sec(
    "Toggle Group",
    "Input",
    "Set of mutually exclusive (single) or additive (multiple) toggles.",
    v(
      "Single — text style",
      shadcn_toggle_group(
        "tgg_fmt",
        list("Bold", "Italic", "Underline"),
        type = "single",
        selected = "Bold"
      )
    ),
    v(
      "Multiple — alignment",
      shadcn_toggle_group(
        "tgg_align",
        list(
          list(value = "left", label = "Left"),
          list(value = "center", label = "Center"),
          list(value = "right", label = "Right"),
          list(value = "justify", label = "Justify")
        ),
        type = "multiple",
        selected = list("left"),
        variant = "outline"
      )
    )
  )
}

sec_calendar <- function() {
  sec(
    "Calendar",
    "Input",
    "Date picker. Server reads input as an ISO string (YYYY-MM-DD).",
    v("Single date", shadcn_calendar("cal_bare"))
  )
}

sec_input_otp <- function() {
  sec(
    "Input OTP",
    "Input",
    "Segmented OTP field. Server reads input as the entered string.",
    v("4 slots", shadcn_input_otp("otp_4", length = 4)),
    v(
      "6 slots with separator",
      shadcn_input_otp("otp_6", length = 6, separator = TRUE)
    )
  )
}

sec_pagination <- function() {
  sec(
    "Pagination",
    "Input",
    "Page-number nav bar. Server reads input as a 1-based int.",
    v(
      "5 pages (no ellipsis)",
      shadcn_pagination(
        "pg_5",
        total_pages = 5L,
        current = 1L,
        show_ellipsis = FALSE
      )
    ),
    v(
      "20 pages with ellipsis",
      shadcn_pagination("pg_20", total_pages = 20L, current = 8L)
    )
  )
}

# ── Display ──────────────────────────────────────────────────────────────────

sec_alert <- function() {
  sec(
    "Alert",
    "Display",
    "Prominent message box. Display-only — no Shiny input.",
    v(
      "Default",
      shadcn_alert("A neutral informational message.", title = "Heads up")
    ),
    v(
      "Destructive",
      shadcn_alert(
        "Something went wrong. Please try again.",
        title = "Error",
        variant = "destructive"
      )
    ),
    v("No title", shadcn_alert("Your changes have been saved successfully."))
  )
}

sec_badge <- function() {
  sec(
    "Badge",
    "Display",
    "Small inline label. Four visual variants.",
    v(
      "All variants",
      tags$div(
        shadcn_badge("Default"),
        shadcn_badge("Secondary", variant = "secondary"),
        shadcn_badge("Destructive", variant = "destructive"),
        shadcn_badge("Outline", variant = "outline"),
        class = "flex gap-2 flex-wrap"
      )
    )
  )
}

sec_avatar <- function() {
  sec(
    "Avatar",
    "Display",
    "User avatar with initials fallback. Three sizes.",
    v(
      "Sizes",
      tags$div(
        shadcn_avatar(fallback = "SM", size = "sm"),
        shadcn_avatar(fallback = "MD"),
        shadcn_avatar(fallback = "LG", size = "lg"),
        class = "flex gap-3 items-center"
      )
    ),
    v(
      "Multiple initials",
      tags$div(
        shadcn_avatar(fallback = "AB"),
        shadcn_avatar(fallback = "JD"),
        shadcn_avatar(fallback = "KL"),
        shadcn_avatar(fallback = "MN"),
        shadcn_avatar(fallback = "ZR"),
        class = "flex gap-2"
      )
    )
  )
}

sec_card <- function() {
  sec(
    "Card",
    "Container",
    "Bordered content container with an optional title header.",
    v(
      "With title",
      shadcn_card(
        tags$div(
          "Card body content goes here.",
          class = "text-sm text-muted-foreground"
        ),
        title = "Card title"
      )
    ),
    v(
      "No header",
      shadcn_card(tags$div("Just a content card, no title.", class = "text-sm"))
    ),
    v(
      "Rich content",
      shadcn_card(
        tags$div(
          shadcn_badge("New", variant = "secondary"),
          tags$h3("Feature update", class = "font-semibold mt-2"),
          tags$div(
            "Version 2.0 is now available.",
            class = "text-sm text-muted-foreground mt-1"
          )
        ),
        title = "Announcement"
      )
    )
  )
}

sec_table <- function() {
  sec(
    "Table",
    "Display",
    "Data table. Columns and rows as lists.",
    v(
      "Sample data",
      shadcn_table(
        columns = c("Name", "Status", "Revenue"),
        rows = list(
          list("Acme Corp", "Active", "$12,400"),
          list("Globex", "Inactive", "$3,200"),
          list("Initech", "Active", "$8,750"),
          list("Umbrella", "Pending", "$5,100"),
          list("Aperture", "Active", "$21,050")
        ),
        caption = "Q4 accounts"
      ),
      wide = TRUE
    )
  )
}

sec_skeleton <- function() {
  sec(
    "Skeleton",
    "Display",
    "Loading placeholder. Shape and size it with class.",
    v(
      "Text block",
      tags$div(
        shadcn_skeleton(class = "h-4 w-full"),
        shadcn_skeleton(class = "h-4 w-5/6"),
        shadcn_skeleton(class = "h-4 w-3/4"),
        shadcn_skeleton(class = "h-4 w-1/2"),
        class = "flex flex-col gap-2 w-full"
      )
    ),
    v(
      "Card",
      tags$div(
        shadcn_skeleton(class = "h-32 w-full rounded-lg"),
        shadcn_skeleton(class = "h-4 w-3/4 mt-3"),
        shadcn_skeleton(class = "h-4 w-1/2 mt-2"),
        class = "w-full"
      )
    ),
    v(
      "Avatar + text",
      tags$div(
        shadcn_skeleton(class = "size-10 rounded-full shrink-0"),
        tags$div(
          shadcn_skeleton(class = "h-4 w-28"),
          shadcn_skeleton(class = "h-3 w-20 mt-1"),
          class = "flex flex-col gap-1 flex-1"
        ),
        class = "flex items-center gap-3 w-full"
      )
    )
  )
}

sec_spinner <- function() {
  sec(
    "Spinner",
    "Display",
    "Animated loading indicator. Size via class (e.g. size-6).",
    v(
      "Sizes",
      tags$div(
        shadcn_spinner(class = "size-4"),
        shadcn_spinner(class = "size-6"),
        shadcn_spinner(class = "size-8"),
        shadcn_spinner(class = "size-12"),
        class = "flex gap-5 items-center"
      )
    )
  )
}

sec_progress <- function() {
  sec(
    "Progress",
    "Display",
    "Determinate progress bar. Value 0–100.",
    v("0%", tags$div(shadcn_progress(0), class = "w-full")),
    v("33%", tags$div(shadcn_progress(33), class = "w-full")),
    v("66%", tags$div(shadcn_progress(66), class = "w-full")),
    v("100%", tags$div(shadcn_progress(100), class = "w-full"))
  )
}

sec_chart <- function() {
  d <- list(
    list(month = "Jan", sales = 120L, returns = 20L),
    list(month = "Feb", sales = 180L, returns = 35L),
    list(month = "Mar", sales = 150L, returns = 28L),
    list(month = "Apr", sales = 210L, returns = 42L),
    list(month = "May", sales = 190L, returns = 31L),
    list(month = "Jun", sales = 240L, returns = 55L)
  )
  s <- list(
    shadcn_chart_series("sales", label = "Sales"),
    shadcn_chart_series("returns", label = "Returns")
  )
  sec(
    "Chart",
    "Display",
    "Recharts wrapper. Four types: bar, line, area, pie.",
    v(
      "Bar",
      shadcn_chart(d, s, type = "bar", x_key = "month", height = 220L),
      wide = TRUE
    ),
    v(
      "Line",
      shadcn_chart(d, s, type = "line", x_key = "month", height = 220L),
      wide = TRUE
    ),
    v(
      "Area",
      shadcn_chart(d, s, type = "area", x_key = "month", height = 220L),
      wide = TRUE
    )
  )
}

sec_separator <- function() {
  sec(
    "Separator",
    "Display",
    "Thin rule for visual separation. Horizontal or vertical.",
    v(
      "Horizontal",
      tags$div(
        tags$div("Section above", class = "text-sm"),
        shadcn_separator(),
        tags$div("Section below", class = "text-sm"),
        class = "flex flex-col gap-3 w-full"
      )
    ),
    v(
      "Vertical (in a flex row)",
      tags$div(
        tags$div("Left", class = "text-sm px-3"),
        shadcn_separator(orientation = "vertical", class = "h-5"),
        tags$div("Center", class = "text-sm px-3"),
        shadcn_separator(orientation = "vertical", class = "h-5"),
        tags$div("Right", class = "text-sm px-3"),
        class = "flex items-center"
      )
    )
  )
}

sec_label <- function() {
  sec(
    "Label",
    "Display",
    "Semantic text label, typically paired with form inputs.",
    v("Standalone", shadcn_label("Email address")),
    v(
      "Stacked list",
      tags$div(
        shadcn_label("First name"),
        shadcn_separator(),
        shadcn_label("Last name"),
        shadcn_separator(),
        shadcn_label("Company"),
        class = "flex flex-col gap-2 w-full"
      )
    )
  )
}

sec_kbd <- function() {
  combo <- function(...) {
    tags$div(..., class = "flex gap-1 items-center")
  }
  plus <- tags$div("+", class = "text-xs text-muted-foreground")
  row <- function(name, keys) {
    tags$div(
      tags$div(name, class = "text-sm"),
      keys,
      class = "flex justify-between items-center"
    )
  }
  sec(
    "Kbd",
    "Display",
    "Keyboard key hint.",
    v(
      "Single keys",
      tags$div(
        shadcn_kbd("⌘"),
        shadcn_kbd("⇧"),
        shadcn_kbd("⌥"),
        shadcn_kbd("⌫"),
        shadcn_kbd("⏎"),
        shadcn_kbd("Esc"),
        class = "flex gap-2 flex-wrap"
      )
    ),
    v(
      "Combos",
      tags$div(
        combo(shadcn_kbd("⌘"), plus, shadcn_kbd("K")),
        combo(shadcn_kbd("⌘"), plus, shadcn_kbd("⇧"), plus, shadcn_kbd("P")),
        class = "flex gap-6"
      )
    ),
    v(
      "In context",
      tags$div(
        row(
          "Save",
          tags$div(shadcn_kbd("⌘"), shadcn_kbd("S"), class = "flex gap-1")
        ),
        row(
          "Open palette",
          tags$div(shadcn_kbd("⌘"), shadcn_kbd("K"), class = "flex gap-1")
        ),
        row(
          "Format",
          tags$div(
            shadcn_kbd("⌘"),
            shadcn_kbd("⇧"),
            shadcn_kbd("F"),
            class = "flex gap-1"
          )
        ),
        class = "flex flex-col gap-2 w-full"
      )
    )
  )
}

sec_empty <- function() {
  sec(
    "Empty",
    "Display",
    "Empty-state panel. Children become the action area.",
    v(
      "With action",
      shadcn_empty(
        shadcn_button("empty_btn_a", "Create item"),
        title = "No items yet",
        description = "Get started by creating your first item."
      )
    ),
    v(
      "Description only",
      shadcn_empty(
        title = "No results found",
        description = "Try adjusting your search or filter."
      )
    )
  )
}

# ── Overlays ─────────────────────────────────────────────────────────────────

sec_dialog <- function() {
  sec(
    "Dialog",
    "Overlay",
    "Modal panel. Server reads input as bool (open state).",
    v(
      "Basic",
      shadcn_dialog(
        "dlg_basic",
        tags$div("Dialog body content goes here.", class = "text-sm"),
        trigger_label = "Open dialog",
        title = "Dialog title",
        description = "Supporting description text."
      )
    ),
    v(
      "With form inputs",
      shadcn_dialog(
        "dlg_form",
        shadcn_input("dlg_name", label = "Name", placeholder = "Your name…"),
        shadcn_slider("dlg_age", min = 18, max = 99, value = 30, label = "Age"),
        shadcn_select(
          "dlg_role",
          list("Engineer", "Designer", "Manager", "Other"),
          label = "Role"
        ),
        trigger_label = "Edit profile",
        title = "Edit profile",
        description = "Update your account information."
      )
    )
  )
}

sec_alert_dialog <- function() {
  sec(
    "Alert Dialog",
    "Overlay",
    "Blocking confirmation. confirm_id increments on confirm.",
    v(
      "Destructive confirm",
      shadcn_alert_dialog(
        "adlg_del",
        trigger_label = "Delete account",
        title = "Delete your account?",
        description = "This action cannot be undone.",
        confirm_label = "Yes, delete"
      )
    ),
    v(
      "Neutral confirm",
      shadcn_alert_dialog(
        "adlg_confirm",
        trigger_label = "Publish post",
        title = "Publish this post?",
        description = "The post will be visible to all users immediately.",
        confirm_label = "Publish"
      )
    )
  )
}

sec_drawer <- function() {
  sec(
    "Drawer",
    "Overlay",
    "Edge-anchored swipe panel (vaul). Server reads open state as bool.",
    v(
      "From bottom",
      shadcn_drawer(
        "drw_bot",
        shadcn_input("drw_search", placeholder = "Search…"),
        shadcn_badge("Drawer content area", variant = "outline"),
        trigger_label = "Open bottom drawer",
        title = "Bottom drawer",
        direction = "bottom"
      )
    ),
    v(
      "From right",
      shadcn_drawer(
        "drw_right",
        shadcn_badge("Right-side content", variant = "secondary"),
        shadcn_input("drw_note", label = "Note", placeholder = "Add a note…"),
        trigger_label = "Open right drawer",
        title = "Right drawer",
        direction = "right"
      )
    )
  )
}

sec_sheet <- function() {
  sec(
    "Sheet",
    "Overlay",
    "Side panel. Slides in from an edge. Server reads open state as bool.",
    v(
      "From right",
      shadcn_sheet(
        "sht_right",
        shadcn_input("sht_name", label = "Name"),
        shadcn_slider(
          "sht_lvl",
          min = 0,
          max = 10,
          value = 5,
          label = "Priority"
        ),
        shadcn_textarea(
          "sht_notes",
          label = "Notes",
          placeholder = "Add notes…"
        ),
        trigger_label = "Open right sheet",
        title = "Edit item",
        side = "right"
      )
    ),
    v(
      "From left",
      shadcn_sheet(
        "sht_left",
        shadcn_badge("Navigation panel", variant = "outline"),
        shadcn_separator(),
        tags$div("Menu item 1", class = "text-sm py-2"),
        tags$div("Menu item 2", class = "text-sm py-2"),
        tags$div("Menu item 3", class = "text-sm py-2"),
        trigger_label = "Open left sheet",
        title = "Navigation",
        side = "left"
      )
    )
  )
}

sec_popover <- function() {
  sec(
    "Popover",
    "Overlay",
    "Small floating panel anchored to a trigger button.",
    v(
      "Default",
      shadcn_popover(
        "pop_basic",
        shadcn_badge("Inside the popover"),
        shadcn_input("pop_input", placeholder = "Type here…"),
        trigger_label = "Open popover"
      )
    ),
    v(
      "Align start",
      shadcn_popover(
        "pop_start",
        tags$div("Anchored to the start edge.", class = "text-sm"),
        shadcn_separator(),
        shadcn_slider(
          "pop_sli",
          min = 0,
          max = 100,
          value = 50,
          label = "Setting"
        ),
        trigger_label = "Anchored popover",
        align = "start"
      )
    )
  )
}

sec_dropdown_menu <- function() {
  sec(
    "Dropdown Menu",
    "Overlay",
    "Contextual action menu. input fires list(value, nonce) on click.",
    v(
      "With groups + separator",
      shadcn_dropdown_menu(
        "ddm_basic",
        shadcn_menu_label("Actions"),
        shadcn_menu_item("edit", "Edit"),
        shadcn_menu_item("duplicate", "Duplicate"),
        shadcn_menu_separator(),
        shadcn_menu_item("delete", "Delete", variant = "destructive"),
        trigger_label = "Open menu"
      )
    ),
    v(
      "With submenu + checkbox",
      shadcn_dropdown_menu(
        "ddm_sub",
        shadcn_menu_item("new", "New file"),
        shadcn_menu_item("open", "Open file…"),
        shadcn_menu_submenu(
          "Move to",
          shadcn_menu_item("inbox", "Inbox"),
          shadcn_menu_item("archive", "Archive"),
          shadcn_menu_item("trash", "Trash")
        ),
        shadcn_menu_separator(),
        shadcn_menu_checkbox("ddm_chk", "Show hidden files"),
        trigger_label = "File menu"
      )
    )
  )
}

sec_context_menu <- function() {
  sec(
    "Context Menu",
    "Overlay",
    "Right-click menu. Children define the trigger area.",
    v(
      "Right-click zone",
      shadcn_context_menu(
        "ctx_basic",
        shadcn_card(
          tags$div(
            "Right-click anywhere in this card",
            class = "text-sm text-muted-foreground py-8 text-center select-none"
          ),
          class = "w-full"
        ),
        items = list(
          shadcn_menu_item("copy", "Copy"),
          shadcn_menu_item("paste", "Paste"),
          shadcn_menu_item("select_all", "Select all"),
          shadcn_menu_separator(),
          shadcn_menu_item("delete", "Delete", variant = "destructive")
        )
      ),
      wide = TRUE
    )
  )
}

sec_tooltip <- function() {
  sec(
    "Tooltip",
    "Overlay",
    "Hover tooltip. Children = trigger element, content = tooltip text.",
    v(
      "Four sides",
      tags$div(
        shadcn_tooltip(
          shadcn_badge("Top"),
          content = "Tooltip on top",
          side = "top"
        ),
        shadcn_tooltip(
          shadcn_badge("Right"),
          content = "Tooltip on right",
          side = "right"
        ),
        shadcn_tooltip(
          shadcn_badge("Bottom"),
          content = "Tooltip on bottom",
          side = "bottom"
        ),
        shadcn_tooltip(
          shadcn_badge("Left"),
          content = "Tooltip on left",
          side = "left"
        ),
        class = "flex gap-3 flex-wrap"
      )
    ),
    v(
      "On a button",
      shadcn_tooltip(
        shadcn_button("tip_btn", "Hover for help"),
        content = "Submits the form and saves your changes",
        side = "top"
      )
    )
  )
}

sec_hover_card <- function() {
  sec(
    "Hover Card",
    "Overlay",
    "Rich card revealed on hover over a trigger link.",
    v(
      "User profile card",
      shadcn_hover_card(
        shadcn_card(
          tags$div(
            tags$div(
              shadcn_avatar(fallback = "SC"),
              tags$div(
                tags$div("@shadcn", class = "font-semibold text-sm"),
                tags$div(
                  "Component library author",
                  class = "text-xs text-muted-foreground"
                ),
                class = "flex flex-col"
              ),
              class = "flex items-center gap-3"
            ),
            tags$div(
              "Building beautiful component libraries for React.",
              class = "text-sm text-muted-foreground mt-2"
            ),
            tags$div(
              shadcn_badge("42 followers", variant = "outline"),
              shadcn_badge("128 following", variant = "outline"),
              class = "flex gap-2 mt-3"
            )
          )
        ),
        trigger_label = "@shadcn"
      )
    )
  )
}

# ── Navigation ───────────────────────────────────────────────────────────────

sec_breadcrumb <- function() {
  sec(
    "Breadcrumb",
    "Navigation",
    "Trail of navigation links. The last item is the current page.",
    v(
      "3-level",
      shadcn_breadcrumb(
        shadcn_crumb("Home", href = "#"),
        shadcn_crumb("Settings", href = "#"),
        shadcn_crumb("Profile")
      )
    ),
    v(
      "Deeper path",
      shadcn_breadcrumb(
        shadcn_crumb("Home", href = "#"),
        shadcn_crumb("Library", href = "#"),
        shadcn_crumb("Components", href = "#"),
        shadcn_crumb("Button")
      )
    )
  )
}

sec_tabs <- function() {
  sec(
    "Tabs",
    "Navigation",
    "Tabbed panel. Active tab tracked as input.",
    v(
      "3 tabs",
      shadcn_tabs(
        "tab_demo",
        tabs = list(
          shadcn_tab("account", "Account"),
          shadcn_tab("password", "Password"),
          shadcn_tab("billing", "Billing")
        ),
        tags$div(
          "Manage your account settings here.",
          class = "text-sm text-muted-foreground py-2"
        ),
        tags$div(
          "Change your password and security settings.",
          class = "text-sm text-muted-foreground py-2"
        ),
        tags$div(
          "View invoices and manage your plan.",
          class = "text-sm text-muted-foreground py-2"
        ),
        selected = "account"
      ),
      wide = TRUE
    )
  )
}

sec_accordion <- function() {
  sec(
    "Accordion",
    "Navigation",
    "Expandable sections. Single or multiple items open at once.",
    v(
      "Single open",
      shadcn_accordion(
        "acc_single",
        items = list(
          shadcn_accordion_item("q1", "Is it accessible?"),
          shadcn_accordion_item("q2", "Is it styled?"),
          shadcn_accordion_item("q3", "Is it animated?")
        ),
        tags$div(
          "Yes. Adheres to the WAI-ARIA design pattern.",
          class = "text-sm"
        ),
        tags$div(
          "Yes. Comes with default styles that match the design.",
          class = "text-sm"
        ),
        tags$div(
          "Yes. Animation handled by CSS transitions.",
          class = "text-sm"
        ),
        type = "single",
        selected = "q1"
      )
    ),
    v(
      "Multiple open",
      shadcn_accordion(
        "acc_multi",
        items = list(
          shadcn_accordion_item("m1", "Section A"),
          shadcn_accordion_item("m2", "Section B"),
          shadcn_accordion_item("m3", "Section C")
        ),
        tags$div("Content for section A.", class = "text-sm"),
        tags$div("Content for section B.", class = "text-sm"),
        tags$div("Content for section C.", class = "text-sm"),
        type = "multiple",
        selected = list("m1", "m3")
      )
    )
  )
}

sec_navigation_menu <- function() {
  sec(
    "Navigation Menu",
    "Navigation",
    "Horizontal nav bar with optional dropdown sub-menus.",
    v(
      "With dropdowns",
      shadcn_navigation_menu(
        shadcn_nav_item(
          "Docs",
          items = list(
            shadcn_nav_item(
              "Introduction",
              href = "#",
              description = "Get started with shinyreact."
            ),
            shadcn_nav_item(
              "Installation",
              href = "#",
              description = "How to install and configure."
            ),
            shadcn_nav_item(
              "Components",
              href = "#",
              description = "Full component reference."
            )
          )
        ),
        shadcn_nav_item("API", href = "#"),
        shadcn_nav_item("GitHub", href = "#")
      ),
      wide = TRUE
    )
  )
}

sec_menubar <- function() {
  sec(
    "Menubar",
    "Navigation",
    "Horizontal menu bar with multiple dropdowns. input fires on item click.",
    v(
      "File / Edit / View",
      shadcn_menubar(
        "mb_demo",
        shadcn_menubar_menu(
          "File",
          shadcn_menu_item("new", "New"),
          shadcn_menu_item("open", "Open…"),
          shadcn_menu_separator(),
          shadcn_menu_item("save", "Save"),
          shadcn_menu_item("saveas", "Save as…"),
          shadcn_menu_separator(),
          shadcn_menu_item("quit", "Quit")
        ),
        shadcn_menubar_menu(
          "Edit",
          shadcn_menu_item("undo", "Undo"),
          shadcn_menu_item("redo", "Redo"),
          shadcn_menu_separator(),
          shadcn_menu_item("cut", "Cut"),
          shadcn_menu_item("copy", "Copy"),
          shadcn_menu_item("paste", "Paste")
        ),
        shadcn_menubar_menu(
          "View",
          shadcn_menu_item("zoom_in", "Zoom In"),
          shadcn_menu_item("zoom_out", "Zoom Out"),
          shadcn_menu_item("reset_zoom", "Reset Zoom"),
          shadcn_menu_separator(),
          shadcn_menu_checkbox("mb_sidebar", "Show Sidebar", checked = TRUE),
          shadcn_menu_checkbox("mb_statusbar", "Show Status Bar")
        )
      ),
      wide = TRUE
    )
  )
}

sec_command <- function() {
  sec(
    "Command",
    "Navigation",
    "Searchable command palette. Server reads input as the selected value.",
    v(
      "With groups + search",
      shadcn_command(
        "cmd_demo",
        items = list(
          list(value = "calendar", label = "Calendar", group = "Suggestions"),
          list(value = "emoji", label = "Search Emoji", group = "Suggestions"),
          list(
            value = "calculator",
            label = "Calculator",
            group = "Suggestions"
          ),
          list(value = "profile", label = "Profile", group = "Settings"),
          list(value = "billing", label = "Billing", group = "Settings"),
          list(value = "settings", label = "Settings", group = "Settings"),
          list(value = "logout", label = "Log out", group = "Settings")
        ),
        placeholder = "Type a command or search…"
      ),
      wide = TRUE
    )
  )
}

sec_collapsible <- function() {
  sec(
    "Collapsible",
    "Navigation",
    "Disclosure widget. Server reads input as bool (open).",
    v(
      "Default closed",
      shadcn_collapsible(
        "col_a",
        tags$div(
          "Hidden content revealed when you click the trigger.",
          class = "text-sm text-muted-foreground"
        ),
        trigger_label = "Show details"
      )
    ),
    v(
      "Default open",
      shadcn_collapsible(
        "col_b",
        tags$div(
          "This content is visible by default.",
          class = "text-sm text-muted-foreground"
        ),
        trigger_label = "Hide details",
        open = TRUE
      )
    )
  )
}

# ── Layout ───────────────────────────────────────────────────────────────────

sec_carousel <- function() {
  slide <- function(txt) {
    shadcn_card(tags$div(txt, class = "p-10 text-center font-semibold text-lg"))
  }
  big <- function(txt) {
    shadcn_card(tags$div(txt, class = "p-10 text-center font-bold text-2xl"))
  }
  sec(
    "Carousel",
    "Layout",
    "Slide carousel (embla). Each child becomes one slide.",
    v(
      "Horizontal (4 slides)",
      shadcn_carousel(
        slide("Slide 1"),
        slide("Slide 2"),
        slide("Slide 3"),
        slide("Slide 4")
      ),
      wide = TRUE
    ),
    v(
      "Loop enabled",
      shadcn_carousel(big("A"), big("B"), big("C"), loop = TRUE)
    )
  )
}

sec_resizable <- function() {
  panel <- function(txt) {
    tags$div(
      txt,
      class = "flex items-center justify-center h-full text-sm font-medium"
    )
  }
  sec(
    "Resizable",
    "Layout",
    "Panels separated by draggable handles.",
    v(
      "2 panels — horizontal",
      tags$div(
        shadcn_resizable(
          panel("Panel A"),
          panel("Panel B"),
          panels = list(list(default_size = 50L), list(default_size = 50L)),
          class = "h-24 rounded-lg border"
        ),
        class = "w-full"
      )
    ),
    v(
      "3 panels",
      tags$div(
        shadcn_resizable(
          panel("A"),
          panel("B"),
          panel("C"),
          panels = list(
            list(default_size = 33L),
            list(default_size = 34L),
            list(default_size = 33L)
          ),
          class = "h-24 rounded-lg border"
        ),
        class = "w-full"
      )
    ),
    v(
      "Vertical split",
      tags$div(
        shadcn_resizable(
          panel("Top"),
          panel("Bottom"),
          orientation = "vertical",
          panels = list(list(default_size = 50L), list(default_size = 50L)),
          class = "h-36 rounded-lg border"
        ),
        class = "w-full"
      )
    )
  )
}

sec_scroll_area <- function() {
  items <- lapply(1:34, function(i) {
    tags$div(
      shadcn_badge(sprintf("Item %02d", i), variant = "outline"),
      class = "py-1"
    )
  })
  tags_h <- lapply(1:23, function(i) {
    shadcn_badge(paste("Tag", i), variant = "secondary")
  })
  sec(
    "Scroll Area",
    "Layout",
    "Scrollable container with styled scrollbar.",
    v(
      "Vertical list",
      do.call(shadcn_scroll_area, c(items, list(height = "200px")))
    ),
    v(
      "Horizontal tags",
      tags$div(
        shadcn_scroll_area(
          do.call(tags$div, c(tags_h, list(class = "flex gap-2 w-max px-1"))),
          orientation = "horizontal",
          height = "40px"
        ),
        class = "w-full"
      )
    )
  )
}

sec_aspect_ratio <- function() {
  box <- function(txt) {
    tags$div(
      tags$div(txt, class = "text-sm font-medium text-muted-foreground"),
      class = "flex items-center justify-center h-full rounded-lg bg-muted"
    )
  }
  sec(
    "Aspect Ratio",
    "Layout",
    "Fixed-ratio container. Children fill the box.",
    v("16:9 — video", shadcn_aspect_ratio(box("16 : 9"), ratio = 16 / 9)),
    v("1:1 — square", shadcn_aspect_ratio(box("1 : 1"), ratio = 1)),
    v("4:3 — classic", shadcn_aspect_ratio(box("4 : 3"), ratio = 4 / 3))
  )
}

# ── Feedback ─────────────────────────────────────────────────────────────────

sec_toaster <- function() {
  sec(
    "Toast (Sonner)",
    "Feedback",
    "Server-push notifications. Mount toaster() once; call shadcn_toast() from the server.",
    v("Default", shadcn_button("toast_default", "Show toast")),
    v(
      "Success",
      shadcn_button("toast_success", "Success", variant = "outline")
    ),
    v("Error", shadcn_button("toast_error", "Error", variant = "outline")),
    v("Info", shadcn_button("toast_info", "Info", variant = "outline")),
    v("Warning", shadcn_button("toast_warning", "Warning", variant = "outline"))
  )
}

# ── Section registry ─────────────────────────────────────────────────────────

SECTIONS <- list(
  inputs = function() {
    list(
      sec_button(),
      sec_text_input(),
      sec_textarea(),
      sec_select(),
      sec_slider(),
      sec_checkbox(),
      sec_switch(),
      sec_radio_group(),
      sec_toggle(),
      sec_toggle_group(),
      sec_calendar(),
      sec_input_otp(),
      sec_pagination()
    )
  },
  display = function() {
    list(
      sec_alert(),
      sec_badge(),
      sec_avatar(),
      sec_card(),
      sec_table(),
      sec_skeleton(),
      sec_spinner(),
      sec_progress(),
      sec_chart(),
      sec_separator(),
      sec_label(),
      sec_kbd(),
      sec_empty()
    )
  },
  overlays = function() {
    list(
      sec_dialog(),
      sec_alert_dialog(),
      sec_drawer(),
      sec_sheet(),
      sec_popover(),
      sec_dropdown_menu(),
      sec_context_menu(),
      sec_tooltip(),
      sec_hover_card()
    )
  },
  nav = function() {
    list(
      sec_breadcrumb(),
      sec_tabs(),
      sec_accordion(),
      sec_navigation_menu(),
      sec_menubar(),
      sec_command(),
      sec_collapsible()
    )
  },
  layout = function() {
    list(sec_carousel(), sec_resizable(), sec_scroll_area(), sec_aspect_ratio())
  },
  feedback = function() list(sec_toaster())
)

CAT_CHOICES <- list(
  list(value = "inputs", label = "Inputs · 13"),
  list(value = "display", label = "Display · 13"),
  list(value = "overlays", label = "Overlays · 9"),
  list(value = "nav", label = "Navigation · 7"),
  list(value = "layout", label = "Layout · 4"),
  list(value = "feedback", label = "Feedback · 1")
)

# ── Server ────────────────────────────────────────────────────────────────────

server <- function(input, output, session) {
  observeEvent(
    input$toast_default,
    {
      shadcn_toast(session, "Event fired!", description = "Button was clicked.")
    },
    ignoreInit = TRUE
  )
  observeEvent(
    input$toast_success,
    {
      shadcn_toast(
        session,
        "Saved!",
        description = "Your changes were saved.",
        type = "success"
      )
    },
    ignoreInit = TRUE
  )
  observeEvent(
    input$toast_error,
    {
      shadcn_toast(
        session,
        "Something went wrong",
        description = "Please try again later.",
        type = "error"
      )
    },
    ignoreInit = TRUE
  )
  observeEvent(
    input$toast_info,
    {
      shadcn_toast(
        session,
        "Did you know?",
        description = "You can stack multiple toasts at once.",
        type = "info"
      )
    },
    ignoreInit = TRUE
  )
  observeEvent(
    input$toast_warning,
    {
      shadcn_toast(
        session,
        "Heads up",
        description = "This action may have side effects.",
        type = "warning"
      )
    },
    ignoreInit = TRUE
  )

  output$gallery <- render_react({
    cat <- if (!is.null(input$cat)) input$cat else "inputs"
    fn <- if (!is.null(SECTIONS[[cat]])) {
      SECTIONS[[cat]]
    } else {
      SECTIONS[["inputs"]]
    }
    sections <- fn()

    tags$div(
      shadcn_toaster(position = "bottom-right"),
      # Hero
      tags$div(
        tags$h1(
          "shadcn x shinyreact",
          class = "text-3xl font-bold tracking-tight"
        ),
        tags$div(
          "47 components · every variant · fully interactive",
          class = "text-muted-foreground mt-2 text-base"
        ),
        class = "flex flex-col pb-6 border-b mb-8"
      ),
      # Category nav
      tags$div(
        shadcn_toggle_group(
          "cat",
          CAT_CHOICES,
          type = "single",
          selected = cat,
          variant = "outline",
          class = "flex-wrap"
        ),
        class = "mb-10"
      ),
      # Content
      do.call(tags$div, c(sections, list(class = "flex flex-col")))
    )
  })
}

shinyApp(ui, server)
