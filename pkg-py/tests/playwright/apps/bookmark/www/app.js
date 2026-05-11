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
    h("h2", null, "Bookmark restoration fixture"),
    h(
      "p",
      null,
      "Open ",
      h(
        "a",
        { href: "?_inputs_&txt=%22hello%22&num=42&chk=true" },
        h("code", null, "?_inputs_&txt=%22hello%22&num=42&chk=true"),
      ),
      " — the three inputs below should preload from the URL and the echo line should read ",
      h("code", null, "text='hello' num=42 checked=yes"),
      ".",
    ),
    h(
      "p",
      null,
      "Open ",
      h("a", { href: "./" }, h("code", null, "/")),
      " — defaults stay in place and ",
      h("code", null, "window.shinyreact._restore"),
      " should equal ",
      h("code", null, '{"-applied":true,"-values":{}}'),
      ".",
    ),
    h(
      "label",
      { "data-row": "txt" },
      h("span", null, "Text"),
      h("input", {
        type: "text",
        "data-testid": "txt",
        value: txt,
        onChange: (e) => setTxt(e.target.value),
      }),
    ),
    h(
      "label",
      { "data-row": "num" },
      h("span", null, "Number"),
      h("input", {
        type: "number",
        "data-testid": "num",
        value: num,
        onChange: (e) => setNum(Number(e.target.value)),
      }),
    ),
    h(
      "label",
      { "data-row": "chk" },
      h("span", null, "Checkbox"),
      h("input", {
        type: "checkbox",
        "data-testid": "chk",
        checked: chk,
        onChange: (e) => setChk(e.target.checked),
      }),
    ),
    h("div", { id: "echo", "data-testid": "echo" }, echo),
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
