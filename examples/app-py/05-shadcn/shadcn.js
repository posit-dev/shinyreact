// 5-shadcn example — shadcn/ui styled cards with shinyreact
// Uses plain HTML + CSS to approximate shadcn look (no build step).
(function () {
  var React = window.shinyreact.React;
  var h = React.createElement;
  var useShinyInput = window.shinyreact.useShinyInput;
  var useShinyOutputValue = window.shinyreact.useShinyOutputValue;
  var ImageOutput = window.shinyreact.ImageOutput;

  // ---------------------------------------------------------------------------
  // PageLayout — registered, invoked from spec
  // ---------------------------------------------------------------------------
  function PageLayout(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "app-container" },
      h(
        "div",
        { className: "app-inner" },
        h(
          "div",
          { className: "app-header" },
          h("h1", { className: "app-title" }, props.title),
          props.subtitle
            ? h("p", { className: "app-subtitle" }, props.subtitle)
            : null
        ),
        h("hr", { className: "separator" }),
        args.children
      )
    );
  }

  // ---------------------------------------------------------------------------
  // Grid — 2-column grid wrapper
  // ---------------------------------------------------------------------------
  function Grid(args) {
    return h("div", { className: "grid-2col" }, args.children);
  }

  // ---------------------------------------------------------------------------
  // TextInputCard
  // ---------------------------------------------------------------------------
  function TextInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, "");
    var inputText = inputResult[0];
    var setInputText = inputResult[1];

    var processedText = useShinyOutputValue(props.processed_output_id, "");

    var textLength = useShinyOutputValue(props.length_output_id, "0");

    function handleInputChange(event) {
      setInputText(event.target.value);
    }

    return h(
      "div",
      { className: "card" },
      h(
        "div",
        { className: "card-header" },
        h("h3", { className: "card-title" }, "Text Input")
      ),
      h(
        "div",
        { className: "card-content" },
        h(
          "div",
          { className: "field" },
          h(
            "label",
            { className: "field-label", htmlFor: "text-input" },
            "Enter some text:"
          ),
          h("input", {
            id: "text-input",
            type: "text",
            className: "input",
            placeholder: "Type something...",
            value: inputText,
            onChange: handleInputChange,
          })
        ),
        h(
          "div",
          { className: "field" },
          h(
            "p",
            { className: "field-description" },
            "Processed text from server:"
          ),
          h(
            "div",
            { className: "muted-box" },
            h(
              "pre",
              { className: "pre-text" },
              processedText || "No text entered yet"
            )
          )
        ),
        h(
          "div",
          { className: "field" },
          h("span", { className: "badge" }, "Length: " + textLength)
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // ButtonEventCard
  // ---------------------------------------------------------------------------
  function ButtonEventCard(args) {
    var props = args.element.props;
    var triggerResult = useShinyInput(props.input_id, 0, { debounceMs: 0, priority: "event" });
    var triggerCount = triggerResult[0];
    var setButtonTrigger = triggerResult[1];

    var buttonResponse = useShinyOutputValue(props.output_id, "");

    function handleClick() {
      setButtonTrigger(triggerCount + 1);
    }

    return h(
      "div",
      { className: "card" },
      h(
        "div",
        { className: "card-header" },
        h("h3", { className: "card-title" }, "Button Events")
      ),
      h(
        "div",
        { className: "card-content" },
        h(
          "div",
          { className: "field" },
          h(
            "p",
            { className: "field-description" },
            "Click to trigger server event:"
          ),
          h(
            "button",
            { className: "button", onClick: handleClick },
            "Send Event"
          )
        ),
        h(
          "div",
          { className: "field" },
          h(
            "p",
            { className: "field-description" },
            "Server response:"
          ),
          h(
            "div",
            { className: "muted-box" },
            h(
              "pre",
              { className: "pre-text" },
              buttonResponse || "Click button to see response"
            )
          )
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // PlotCard
  // ---------------------------------------------------------------------------
  function PlotCard(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "card" },
      h(
        "div",
        { className: "card-header" },
        h("h3", { className: "card-title" }, "Plot Output")
      ),
      h(
        "div",
        { className: "card-content" },
        h(
          "div",
          { className: "plot-container" },
          h(ImageOutput, { id: props.plot_id, className: "plot-image" })
        )
      )
    );
  }

  // Register all components with shinyreact
  window.shinyreact.registerComponents(null, {
    PageLayout: PageLayout,
    Grid: Grid,
    TextInputCard: TextInputCard,
    ButtonEventCard: ButtonEventCard,
    PlotCard: PlotCard,
  });
})();
