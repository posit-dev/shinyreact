// 2-inputs example — registers all input card components with shinyjson.
// Converted from the upstream shiny-react TypeScript example to plain JS
// using React.createElement (no JSX, no build step).
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useState = React.useState;
  var useRef = React.useRef;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;

  // ---------------------------------------------------------------------------
  // Card — simple wrapper with a title
  // ---------------------------------------------------------------------------
  function Card(props) {
    return h(
      "div",
      { className: "card" },
      h("h2", null, props.title),
      props.children
    );
  }

  // ---------------------------------------------------------------------------
  // InputOutputCard — shows input on one side, server response on the other
  // ---------------------------------------------------------------------------
  function InputOutputCard(props) {
    var layout = props.layout || "horizontal";
    var containerClass =
      layout === "vertical"
        ? "input-output-container-vertical"
        : "input-output-container";

    return h(
      Card,
      { title: props.title },
      h(
        "div",
        { className: containerClass },
        h("div", { className: "input-group" }, props.inputElement),
        h(
          "div",
          { className: "output-section" },
          h("div", { className: "output-label" }, "Server response:"),
          h("div", { className: "output-content" }, props.outputValue)
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // PageLayout — registered, invoked from spec
  // ---------------------------------------------------------------------------
  function PageLayout(args) {
    var props = args.element.props;
    return h(
      "div",
      { className: "app-container" },
      h("h1", null, props.title),
      h("div", { className: "cards-wrap" }, args.children)
    );
  }

  // ---------------------------------------------------------------------------
  // TextInputCard
  // ---------------------------------------------------------------------------
  function TextInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value || "");
    var txtin = inputResult[0];
    var setTxtin = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var txtout = outputResult[0];

    function handleInputChange(event) {
      setTxtin(event.target.value);
    }

    return h(InputOutputCard, {
      title: "Text Input",
      inputElement: h("input", {
        type: "text",
        value: txtin,
        onChange: handleInputChange,
        placeholder: "Enter your message here...",
      }),
      outputValue: txtout,
    });
  }

  // ---------------------------------------------------------------------------
  // NumberInputCard
  // ---------------------------------------------------------------------------
  function NumberInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value != null ? props.default_value : 0);
    var numberIn = inputResult[0];
    var setNumberIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var numberOut = outputResult[0];

    function handleInputChange(event) {
      setNumberIn(Number(event.target.value));
    }

    return h(InputOutputCard, {
      title: "Number Input",
      inputElement: h("input", {
        type: "number",
        value: numberIn,
        onChange: handleInputChange,
        min: "0",
        max: "100",
        step: "1",
      }),
      outputValue: numberOut,
    });
  }

  // ---------------------------------------------------------------------------
  // CheckboxInputCard
  // ---------------------------------------------------------------------------
  function CheckboxInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value != null ? props.default_value : false, { debounceMs: 0 });
    var checkboxIn = inputResult[0];
    var setCheckboxIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var checkboxOut = outputResult[0];

    function handleInputChange(event) {
      setCheckboxIn(event.target.checked);
    }

    return h(InputOutputCard, {
      title: "Checkbox Input",
      inputElement: h(
        "div",
        null,
        h(
          "label",
          null,
          h("input", {
            id: "checkbox-input",
            type: "checkbox",
            checked: checkboxIn,
            onChange: handleInputChange,
            className: "checkbox-input",
          }),
          "Enable feature"
        )
      ),
      outputValue: checkboxOut,
    });
  }

  // ---------------------------------------------------------------------------
  // RadioInputCard
  // ---------------------------------------------------------------------------
  function RadioInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value || "option1", { debounceMs: 0 });
    var radioIn = inputResult[0];
    var setRadioIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var radioOut = outputResult[0];

    function handleInputChange(event) {
      setRadioIn(event.target.value);
    }

    function radioOption(value, label) {
      return h(
        "label",
        { className: "radio-label" },
        h("input", {
          type: "radio",
          name: "radio-options",
          value: value,
          checked: radioIn === value,
          onChange: handleInputChange,
          className: "radio-input",
        }),
        label
      );
    }

    return h(InputOutputCard, {
      title: "Radio Button Input",
      inputElement: h(
        "div",
        { className: "radio-group" },
        radioOption("option1", "Option 1"),
        radioOption("option2", "Option 2"),
        radioOption("option3", "Option 3")
      ),
      outputValue: radioOut,
    });
  }

  // ---------------------------------------------------------------------------
  // SelectInputCard
  // ---------------------------------------------------------------------------
  function SelectInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value || "apple", { debounceMs: 0 });
    var selectIn = inputResult[0];
    var setSelectIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var selectOut = outputResult[0];

    function handleInputChange(event) {
      setSelectIn(event.target.value);
    }

    return h(InputOutputCard, {
      title: "Select Input",
      inputElement: h(
        "select",
        {
          value: selectIn,
          onChange: handleInputChange,
          className: "select-input",
        },
        h("option", { value: "apple" }, "Apple"),
        h("option", { value: "banana" }, "Banana"),
        h("option", { value: "orange" }, "Orange"),
        h("option", { value: "grape" }, "Grape"),
        h("option", { value: "mango" }, "Mango")
      ),
      outputValue: selectOut,
    });
  }

  // ---------------------------------------------------------------------------
  // SliderInputCard
  // ---------------------------------------------------------------------------
  function SliderInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, props.default_value != null ? props.default_value : 50, { debounceMs: 0 });
    var sliderIn = inputResult[0];
    var setSliderIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var sliderOut = outputResult[0];

    function handleInputChange(event) {
      setSliderIn(Number(event.target.value));
    }

    return h(InputOutputCard, {
      title: "Slider Input",
      inputElement: h(
        "div",
        null,
        h("label", null, "Adjust the slider (0-100):"),
        h("input", {
          type: "range",
          min: "0",
          max: "100",
          value: sliderIn,
          onChange: handleInputChange,
          className: "slider-input",
        }),
        h("div", { className: "slider-value" }, "Current value: " + sliderIn),
        h(
          "div",
          { className: "note" },
          "Note: Debounce is set to 0ms for immediate updates"
        )
      ),
      outputValue: sliderOut,
    });
  }

  // ---------------------------------------------------------------------------
  // DateInputCard
  // ---------------------------------------------------------------------------
  function DateInputCard(args) {
    var props = args.element.props;
    var today = new Date().toISOString().split("T")[0];

    var inputResult = useShinyInput(props.input_id, props.default_value || today, { debounceMs: 0 });
    var dateIn = inputResult[0];
    var setDateIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, undefined);
    var dateOut = outputResult[0];

    function handleInputChange(event) {
      setDateIn(event.target.value);
    }

    return h(InputOutputCard, {
      title: "Date Input",
      inputElement: h(
        "div",
        null,
        h("label", null, "Select a date:"),
        h("input", {
          type: "date",
          value: dateIn,
          onChange: handleInputChange,
          className: "date-input",
        }),
        h("div", { className: "date-value" }, "Selected date: " + dateIn)
      ),
      outputValue: dateOut,
    });
  }

  // ---------------------------------------------------------------------------
  // ButtonInputCard
  // ---------------------------------------------------------------------------
  function ButtonInputCard(args) {
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, 0);
    var buttonIn = inputResult[0];
    var setButtonIn = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, 0);
    var buttonOut = outputResult[0];

    function handleButtonClick() {
      setButtonIn(buttonIn + 1);
    }

    return h(InputOutputCard, {
      title: "Button Input",
      inputElement: h(
        "div",
        null,
        h(
          "button",
          {
            type: "button",
            onClick: handleButtonClick,
            className: "button-input",
          },
          "Click Me"
        ),
        h(
          "div",
          { className: "button-value" },
          "Click count: " + buttonIn
        ),
        h(
          "div",
          { className: "note" },
          "Note: useShinyInput starts at 0 and increments on click, matching Shiny's action button pattern."
        )
      ),
      outputValue: buttonOut,
    });
  }

  // ---------------------------------------------------------------------------
  // FileInputCard
  // ---------------------------------------------------------------------------
  function FileInputCard(args) {
    var inputRef = useRef(null);
    var filesState = useState([]);
    var files = filesState[0];
    var setFiles = filesState[1];
    var dragState = useState(false);
    var isDragOver = dragState[0];
    var setIsDragOver = dragState[1];

    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, null, { debounceMs: 0 });
    var setFilein = inputResult[1];
    var outputResult = useShinyOutput(props.output_id, undefined);
    var fileout = outputResult[0];

    function handleFileList(fileList) {
      if (fileList && fileList.length > 0) {
        var fileArray = Array.from(fileList);
        setFiles(fileArray);
        // Send file metadata to the server via useShinyInput
        var fileInfo = fileArray.map(function (file) {
          return { name: file.name, size: file.size, type: file.type };
        });
        setFilein(fileInfo);
      } else {
        setFiles([]);
        setFilein(null);
      }
    }

    function handleInputChange(event) {
      handleFileList(event.target.files);
    }

    function handleButtonClick() {
      if (inputRef.current) {
        inputRef.current.click();
      }
    }

    function handleDragOver(event) {
      event.preventDefault();
      setIsDragOver(true);
    }

    function handleDragLeave(event) {
      event.preventDefault();
      setIsDragOver(false);
    }

    function handleDrop(event) {
      event.preventDefault();
      setIsDragOver(false);
      handleFileList(event.dataTransfer.files);
    }

    var dropZoneContent;
    if (files.length === 0) {
      dropZoneContent = h(
        "div",
        { className: "file-drop-content" },
        h(
          "div",
          { className: "file-drop-text" },
          "Click to select files or drag and drop them here"
        ),
        h(
          "div",
          { className: "file-drop-hint" },
          "Multiple files are supported"
        )
      );
    } else {
      dropZoneContent = h(
        "div",
        { className: "file-drop-content" },
        h(
          "div",
          { className: "selected-files" },
          h(
            "ul",
            { className: "selected-files-list" },
            files.map(function (file, index) {
              return h(
                "li",
                { key: index },
                file.name + " (" + Math.round(file.size / 1024) + " KB)"
              );
            })
          ),
          h(
            "div",
            { className: "file-drop-hint" },
            "Click to select different files or drag new ones here"
          )
        )
      );
    }

    var inputElement = h(
      "div",
      null,
      h("input", {
        ref: inputRef,
        type: "file",
        multiple: true,
        onChange: handleInputChange,
        style: { display: "none" },
      }),
      // Custom drag and drop area
      h(
        "div",
        {
          className: "file-drop-zone" + (isDragOver ? " drag-over" : ""),
          onDragOver: handleDragOver,
          onDragLeave: handleDragLeave,
          onDrop: handleDrop,
          onClick: handleButtonClick,
        },
        dropZoneContent
      )
    );

    var outputElement = h(
      "pre",
      { className: "code-output" },
      JSON.stringify(fileout, null, 2)
    );

    return h(InputOutputCard, {
      title: "File Input",
      inputElement: inputElement,
      outputValue: outputElement,
      layout: "vertical",
    });
  }

  // ---------------------------------------------------------------------------
  // BatchFormCard
  // ---------------------------------------------------------------------------
  function BatchFormCard(args) {
    // Local state (NOT Shiny inputs)
    var commentState = useState("");
    var comment = commentState[0];
    var setComment = commentState[1];

    var priorityState = useState(50);
    var priority = priorityState[0];
    var setPriority = priorityState[1];

    var featuresState = useState({
      authentication: false,
      notifications: false,
      darkMode: false,
      analytics: false,
    });
    var features = featuresState[0];
    var setFeatures = featuresState[1];

    // Shiny input/output for batch submission
    var props = args.element.props;
    var inputResult = useShinyInput(props.input_id, null, {
      debounceMs: 0,
      priority: "event",
    });
    var setBatchData = inputResult[1];

    var outputResult = useShinyOutput(props.output_id, "");
    var batchOutput = outputResult[0];

    function handleFeatureChange(feature) {
      setFeatures(function (prev) {
        var next = {};
        for (var key in prev) {
          next[key] = prev[key];
        }
        next[feature] = !prev[feature];
        return next;
      });
    }

    function handleSubmit() {
      var formData = {
        comment: comment,
        priority: priority,
        features: features,
      };
      setBatchData(formData);
    }

    var selectedFeaturesCount = Object.values(features).filter(Boolean).length;

    var featureEntries = Object.entries(features);
    var checkboxItems = featureEntries.map(function (entry) {
      var feature = entry[0];
      var checked = entry[1];
      return h(
        "label",
        { key: feature, className: "checkbox-item" },
        h("input", {
          type: "checkbox",
          checked: checked,
          onChange: function () {
            handleFeatureChange(feature);
          },
        }),
        feature.charAt(0).toUpperCase() + feature.slice(1)
      );
    });

    var inputElement = h(
      "div",
      { className: "batch-form" },
      // Comment
      h(
        "div",
        { className: "form-group" },
        h("label", null, "Comment:"),
        h("textarea", {
          value: comment,
          onChange: function (e) {
            setComment(e.target.value);
          },
          placeholder: "Enter your feedback or description...",
          rows: 3,
        })
      ),
      // Priority slider
      h(
        "div",
        { className: "form-group" },
        h("label", null, "Priority: " + priority + "%"),
        h("input", {
          className: "slider-input",
          type: "range",
          min: "0",
          max: "100",
          value: priority,
          onChange: function (e) {
            setPriority(Number(e.target.value));
          },
        })
      ),
      // Features checkboxes
      h(
        "div",
        { className: "form-group" },
        h("label", null, "Select Features:"),
        h("div", { className: "checkbox-group" }, checkboxItems)
      ),
      // Summary
      h(
        "div",
        { className: "form-summary" },
        h(
          "small",
          null,
          "Summary: " +
            comment.length +
            " characters, " +
            priority +
            "% priority, " +
            selectedFeaturesCount +
            " features selected"
        )
      ),
      // Submit button
      h(
        "button",
        {
          onClick: handleSubmit,
          className: "submit-button",
          disabled: !comment.trim(),
        },
        "Submit Form Data"
      ),
      h(
        "div",
        { className: "note" },
        "Shiny input value is set only when the button is clicked, and it includes an aggregation of all of the values from above."
      )
    );

    var outputElement = h(
      "pre",
      { className: "code-output" },
      JSON.stringify(batchOutput, null, 2)
    );

    return h(InputOutputCard, {
      title: "Batch Form Submission",
      inputElement: inputElement,
      outputValue: outputElement,
    });
  }

  // Register all components with shinyjson
  window.shinyjson.registerComponents(null, {
    PageLayout: PageLayout,
    TextInputCard: TextInputCard,
    NumberInputCard: NumberInputCard,
    CheckboxInputCard: CheckboxInputCard,
    RadioInputCard: RadioInputCard,
    SelectInputCard: SelectInputCard,
    SliderInputCard: SliderInputCard,
    DateInputCard: DateInputCard,
    ButtonInputCard: ButtonInputCard,
    FileInputCard: FileInputCard,
    BatchFormCard: BatchFormCard,
  });
})();
