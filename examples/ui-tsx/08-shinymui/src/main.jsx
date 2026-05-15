import { App } from "./App.jsx";

const { React, ReactDOM } = window.shinyreact;
const h = React.createElement;

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
