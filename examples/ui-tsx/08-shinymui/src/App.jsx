const { React, useShinyInitialized, ShinyOutput } = window.shinyreact;
const h = React.createElement;

const containerStyle = {
  padding: "16px",
  fontFamily: "sans-serif",
  display: "flex",
  flexDirection: "column",
  gap: "16px",
  maxWidth: "800px",
  margin: "0 auto",
};

/**
 * The page shell is hand-written React. Each `<ShinyOutput>` mounts a div
 * carrying the `shinyreact-output` class so shinyreact's existing
 * OutputBinding picks it up and renders the latest server-sent Spec via the
 * registered shinymui catalog (loaded via `shinymui.dep()`).
 */
export function App() {
  const initialized = useShinyInitialized();
  if (!initialized) return null;

  return h(
    "div",
    { style: containerStyle },
    h("h1", null, "shinymui — ui.tsx pattern"),
    h(ShinyOutput, {
      id: "controls_card",
      className: "shinyreact-output",
    }),
    h(ShinyOutput, {
      id: "data_card",
      className: "shinyreact-output",
    }),
  );
}
