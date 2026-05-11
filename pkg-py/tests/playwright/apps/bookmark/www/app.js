const {
  React,
  ReactDOM,
  useShinyInput,
  useSetShinyInput,
  useShinyOutputValue,
} = window.shinyreact;
const h = React.createElement;

function App() {
  // Hooks called unconditionally on every render — Rules of Hooks. They
  // internally gate their Shiny side-effects on useShinyInitialized, so it
  // is safe to render the inputs before the websocket connects.
  const [txt, setTxt] = useShinyInput("txt", "");
  const [num, setNum] = useShinyInput("num", 0);
  const [chk, setChk] = useShinyInput("chk", false);
  const setBookmarkClicks = useSetShinyInput("bookmark_clicks", 0, {
    debounceMs: 0,
    priority: "event",
  });
  const echo = useShinyOutputValue("echo", "");
  const clicksRef = React.useRef(0);

  return h(
    "div",
    null,
    h(
      "p",
      null,
      "Bookmark-restoration fixture. Loading ",
      h("code", null, "?_inputs_&txt=%22hello%22&num=42&chk=true"),
      " should populate the three inputs from the URL and the echo line",
      " below should read ",
      h("code", null, "text='hello' num=42 checked=yes"),
      ". Loading the plain URL should leave defaults in place and set",
      " ",
      h("code", null, 'window.shinyreact._restore = {"-applied":true,"-values":{}}'),
      ".",
    ),
    h("input", {
      type: "text",
      "data-testid": "txt",
      value: txt,
      onChange: (e) => setTxt(e.target.value),
    }),
    h("input", {
      type: "number",
      "data-testid": "num",
      value: num,
      onChange: (e) => setNum(Number(e.target.value)),
    }),
    h("input", {
      type: "checkbox",
      "data-testid": "chk",
      checked: chk,
      onChange: (e) => setChk(e.target.checked),
    }),
    h("div", { "data-testid": "echo" }, echo),
    h(
      "button",
      {
        "data-testid": "bookmark-btn",
        onClick: () => {
          clicksRef.current += 1;
          setBookmarkClicks(clicksRef.current);
        },
      },
      "Bookmark",
    ),
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
