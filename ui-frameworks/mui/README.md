# shinymui

MUI (Material UI) components for shinyreact.

Unlike shadcn, MUI is a real npm package — no source to copy in. Wrappers live
in `js/src/wrappers/` and import from `@mui/material`.

## Status

Scaffold ready. No components wrapped yet.

To add components, use the `/scaffold-component` skill:

> "Add a Button component to mui"

## Build

```bash
cd js
npm install
npm run build    # → www/mui.js
```

## Reference

- MUI docs: https://mui.com/material-ui/
- Barret's prototype: `origin/schloerke/react-ui-frameworks` →
  `downstream-prototypes/shinymui/` (Button, Card, Slider, TextField, DataGrid)
