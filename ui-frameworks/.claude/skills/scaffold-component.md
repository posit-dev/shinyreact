# scaffold-component

Add one new component to an existing ui-frameworks framework (shadcn, mui, etc.).

## When to use

When the user says "add a `<ComponentName>` component to shadcn" (or another framework), or "wrap `<LibraryComponent>` for shinyreact."

## Inputs needed

- **framework** — directory name under `ui-frameworks/` (e.g. `shadcn`, `mui`)
- **component_name** — PascalCase component name (e.g. `Select`, `Slider`)
- **hook** — which Shiny hook it needs:
  - `none` — display-only (Badge, Separator pattern)
  - `useShinyInput` — two-way text/value input (Input pattern)
  - `useSetShinyInput` — event/action input (Button pattern)
  - `useShinyOutputValue` — server-driven display (reads a reactive_output)

## Steps

### 1. Write the wrapper

Create `ui-frameworks/<framework>/js/src/wrappers/<ComponentName>.jsx`:

```jsx
import { <ComponentName> as Lib<ComponentName> } from "@/components/<component-name>";

// For useShinyInput / useSetShinyInput:
const { useShinyInput } = window.shinyreact;

// Server props: document each prop with name, type, default
// input_id (str), default_value (str, default ""), ...
export function <ComponentName>({ element, children }) {
  const p = element.props;
  // wire hook here
  return <Lib<ComponentName> ...>{children}</Lib<ComponentName>>;
}
```

**Hook patterns:**

```jsx
// Event input (Button pattern — increment on action):
const [count, setCount] = useSetShinyInput(p.input_id, 0, { debounceMs: 0, priority: "event" });

// Two-way input (Input pattern):
const [value, setValue] = useShinyInput(p.input_id, p.default_value ?? "", { debounceMs: p.debounce_ms ?? 250 });

// Server-driven display:
const { useShinyOutputValue } = window.shinyreact;
const value = useShinyOutputValue(p.output_id, p.default_value ?? null);
```

### 2. Register in index.jsx

Add to `ui-frameworks/<framework>/js/src/index.jsx`:

```jsx
import { <ComponentName> } from "@/wrappers/<ComponentName>";
// in registerComponents call:
"<framework>:<ComponentName>": <ComponentName>,
```

### 3. Add Python helper

Add to `ui-frameworks/<framework>/pkg-py/__init__.py`:

```python
def <snake_name>(input_id: str, ...) -> shinyreact.Node:
    """<One-line description>.

    Args:
        input_id: Shiny input id.
        ...
    """
    return shinyreact.Node(
        type="<framework>:<ComponentName>",
        props={"input_id": input_id, ...},
    )
```

### 4. Add R helper

Add to `ui-frameworks/<framework>/pkg-r/<framework>.R`:

```r
#' <One-line description>.
#'
#' @param input_id Shiny input id.
shadcn_<snake_name> <- function(input_id, ...) {
  node("<framework>:<ComponentName>", props = list(input_id = input_id, ...))
}
```

### 5. Copy source component (shadcn only)

shadcn components are copy-pasted source. If the component is not already in
`js/src/components/`, run the shadcn CLI or manually copy the source file:

```bash
# from the framework's js/ directory:
npx shadcn@latest add <component-name>
# then move from components/ui/ → src/components/
```

### 6. Verify

```bash
cd ui-frameworks/<framework>/js && npm run build
```

Check `www/<framework>.js` was produced with no errors.

## Naming conventions

- JS registration key: `"<framework>:<ComponentName>"` (e.g. `"shadcn:Select"`)
- Python function: `<snake_framework>_<snake_name>` (e.g. `shadcn_select`)
- R function: same as Python
- Server props: `snake_case` (e.g. `input_id`, `default_value`, `debounce_ms`)
