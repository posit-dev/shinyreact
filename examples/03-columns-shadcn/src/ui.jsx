import "@/index.css";

import App from "@/App";

const { React, ReactDOM } = window.shinyreact;

// This example owns www/index.html, so the mount point already exists (and
// shows "Loading…" until we get here). Examples without an HTML document
// append their own container instead.
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(React.createElement(App));
