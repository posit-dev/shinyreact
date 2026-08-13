const { React, ReactDOM, useShinyInput, useShinyOutputValue, useShinyInitialized } =
  window.shinyreact;

const h = React.createElement;

const C_MIN = -40;
const C_MAX = 60;
const F_MIN = -40;
const F_MAX = 140;

const cToF = (c) => Math.round((c * 9) / 5 + 32);
const fToC = (f) => Math.round(((f - 32) * 5) / 9);

function zoneColor(c) {
  if (c <= 0) return "#0dcaf0";
  if (c <= 15) return "#0d6efd";
  if (c <= 30) return "#198754";
  return "#dc3545";
}
function zoneLabel(c) {
  if (c <= 0) return "Freezing";
  if (c <= 15) return "Cold";
  if (c <= 30) return "Comfortable";
  return "Hot";
}

function Thermometer({ label, value, onChange, min, max, unit }) {
  return h(
    "div",
    { className: "thermometer" },
    h("div", { className: "thermo-label" }, label),
    h("div", { className: "thermo-value" }, value + unit),
    h(
      "div",
      { className: "thermo-slider-wrap" },
      h("span", { className: "thermo-tick" }, max),
      h("input", {
        type: "range",
        className: "thermo-slider",
        min,
        max,
        value,
        onInput: (e) => onChange(Number(e.target.value)),
      }),
      h("span", { className: "thermo-tick" }, min),
    ),
  );
}

function App() {
  const initialized = useShinyInitialized();
  const [celsius, setCelsius] = useShinyInput("celsius", 20, { debounceMs: 0 });
  const display = useShinyOutputValue("display", null);

  if (!initialized) return null;

  const fahrenheit = cToF(celsius);
  const color = zoneColor(celsius);
  const zone = zoneLabel(celsius);

  return h(
    "div",
    { className: "temp-card" },
    h("h2", { className: "temp-title" }, "Temperature Converter"),
    h(
      "div",
      { className: "temp-display" },
      h(
        "span",
        { className: "temp-reading" },
        `${celsius}°C = ${fahrenheit}°F`,
      ),
      h(
        "span",
        { className: "temp-badge", style: { backgroundColor: color } },
        zone,
      ),
    ),
    display
      ? h(
          "div",
          { className: "server-echo" },
          `Server: ${display.celsius}°C → ${display.fahrenheit}°F (${display.zone})`,
        )
      : null,
    h(
      "div",
      { className: "thermo-row" },
      h(Thermometer, {
        label: "Celsius",
        value: celsius,
        onChange: setCelsius,
        min: C_MIN,
        max: C_MAX,
        unit: "°C",
      }),
      h(Thermometer, {
        label: "Fahrenheit",
        value: fahrenheit,
        onChange: (f) => setCelsius(fToC(f)),
        min: F_MIN,
        max: F_MAX,
        unit: "°F",
      }),
    ),
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(h(App));
