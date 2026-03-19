// 3-outputs example — registers components with shinyjson
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;
  var ImageOutput = window.shinyjson.ImageOutput;

  // ---------------------------------------------------------------------------
  // Card — generic wrapper
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
  // SliderCard — input control for row count
  // ---------------------------------------------------------------------------
  function SliderCard() {
    var result = useShinyInput("table_rows", 4);
    var rowCount = result[0];
    var setRowCount = result[1];

    return h(
      Card,
      { title: "Data Control" },
      h(
        "div",
        { className: "input-section" },
        h(
          "label",
          { htmlFor: "row-slider" },
          "Number of rows to load: " + rowCount
        ),
        h("input", {
          id: "row-slider",
          type: "range",
          min: "1",
          max: "32",
          value: rowCount,
          onChange: function (e) {
            setRowCount(parseInt(e.target.value));
          },
          className: "slider",
        })
      )
    );
  }

  // ---------------------------------------------------------------------------
  // StatisticsCard — displays stats from useShinyOutput
  // ---------------------------------------------------------------------------
  function StatisticsCard() {
    var result = useShinyOutput("table_stats", undefined);
    var tableStats = result[0];

    if (!tableStats) {
      return h(
        Card,
        { title: "Statistics" },
        h(
          "div",
          { className: "output-section" },
          h(
            "div",
            { className: "stats-placeholder" },
            "Loading statistics..."
          )
        )
      );
    }

    var range = tableStats.max - tableStats.min;
    var meanPct = ((tableStats.mean - tableStats.min) / range) * 100;
    var medianPct = ((tableStats.median - tableStats.min) / range) * 100;

    return h(
      Card,
      { title: "Statistics" },
      h(
        "div",
        { className: "output-section" },
        h(
          "div",
          { className: "stats-section" },
          h("h3", null, tableStats.colname + " statistics"),
          h(
            "div",
            { className: "stats-visual" },
            h(
              "div",
              { className: "stat-range" },
              h(
                "div",
                { className: "range-bar" },
                h(
                  "div",
                  { className: "range-track" },
                  h(
                    "span",
                    { className: "range-min" },
                    tableStats.min.toFixed(1)
                  ),
                  h(
                    "span",
                    { className: "range-max" },
                    tableStats.max.toFixed(1)
                  )
                ),
                h(
                  "div",
                  {
                    className: "range-indicator mean-indicator",
                    style: { left: meanPct + "%" },
                    title: "Mean: " + tableStats.mean.toFixed(2),
                  },
                  h("div", { className: "indicator-dot mean-dot" }),
                  h(
                    "div",
                    { className: "indicator-label" },
                    "Mean",
                    h("br"),
                    tableStats.mean.toFixed(1)
                  )
                ),
                h(
                  "div",
                  {
                    className: "range-indicator median-indicator",
                    style: { left: medianPct + "%" },
                    title: "Median: " + tableStats.median.toFixed(2),
                  },
                  h("div", { className: "indicator-dot median-dot" }),
                  h(
                    "div",
                    { className: "indicator-label" },
                    "Median",
                    h("br"),
                    tableStats.median.toFixed(1)
                  )
                )
              )
            )
          )
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // DataTableCard — renders table data from useShinyOutput
  // ---------------------------------------------------------------------------
  function DataTableCard() {
    var result = useShinyOutput("table_data", undefined);
    var tableData = result[0];

    var columnNames = tableData ? Object.keys(tableData) : [];
    var numRows =
      columnNames.length > 0 && tableData
        ? tableData[columnNames[0]].length
        : 0;

    var headerCells = columnNames.map(function (colName) {
      return h("th", { key: colName }, colName.toUpperCase());
    });

    var rows = [];
    for (var i = 0; i < numRows; i++) {
      (function (rowIndex) {
        var cells = columnNames.map(function (colName) {
          var value = tableData[colName][rowIndex];
          var display =
            typeof value === "number"
              ? Number.isInteger(value)
                ? value
                : value.toFixed(3)
              : value;
          return h("td", { key: colName }, display);
        });
        rows.push(h("tr", { key: rowIndex }, cells));
      })(i);
    }

    return h(
      Card,
      { title: "Table Data" },
      h(
        "div",
        { className: "output-section" },
        h("h3", null, numRows + " rows from mtcars dataset"),
        h(
          "div",
          { className: "table-container", style: { "--max-rows": 8 } },
          h(
            "table",
            { className: "data-table" },
            h("thead", null, h("tr", null, headerCells)),
            h("tbody", null, rows)
          )
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // PlotCard — renders matplotlib plot via ImageOutput
  // ---------------------------------------------------------------------------
  function PlotCard() {
    return h(
      Card,
      { title: "Plot output" },
      h(
        "div",
        { className: "plot-container" },
        h(ImageOutput, { id: "plot1", className: "data-plot" })
      )
    );
  }

  // ---------------------------------------------------------------------------
  // App — top-level layout
  // ---------------------------------------------------------------------------
  function App() {
    return h(
      "div",
      { className: "app-container" },
      h("h1", null, "Shiny React Output Examples"),
      h(
        "div",
        { className: "cards-wrap" },
        h(SliderCard),
        h(StatisticsCard),
        h(DataTableCard),
        h(PlotCard)
      )
    );
  }

  // Register all components
  window.shinyjson.registerComponents(null, {
    App: App,
    Card: Card,
    SliderCard: SliderCard,
    StatisticsCard: StatisticsCard,
    DataTableCard: DataTableCard,
    PlotCard: PlotCard,
  });
})();
