// DEV path. The hooks come from the vendored shiny-react source and are bundled
// with this example's OWN dev React (Fast Refresh needs a dev React build;
// window.shinyreact.React is production). `resolve.dedupe` in vite.config keeps
// these and App.tsx on a single React copy. The relative path reaches the
// vendored source at the repo's pkg-js/src/shiny-react/ (served thanks to
// server.fs.allow in vite.config). Downstream apps would import a published
// @posit/shiny-react instead.
export {
  useShinyInitialized,
  useShinyInput,
  useShinyOutputValue,
} from "../../../../pkg-js/src/shiny-react/index";
