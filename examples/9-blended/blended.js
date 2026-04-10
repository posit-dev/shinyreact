// Blended example — sidebar layout with 3 tabbed panels mixing
// React inputs (useShinyInput) and Shiny outputs (useShinyOutput, ImageOutput).
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useState = React.useState;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;
  var ImageOutput = window.shinyjson.ImageOutput;

  // ── SVG Icons ──────────────────────────────────────────────────────────
  var chartIcon = h(
    "svg",
    { width: 20, height: 20, viewBox: "0 0 448 512", fill: "currentColor" },
    h("path", {
      d: "M160 32v448H48a48 48 0 01-48-48V80a48 48 0 0148-48h112zm64 0h112a48 48 0 0148 48v352a48 48 0 01-48 48H224V32zm-32 0h0v480h0V32z",
    })
  );
  var tableIcon = h(
    "svg",
    { width: 20, height: 20, viewBox: "0 0 512 512", fill: "currentColor" },
    h("path", {
      d: "M64 256V160H224v96H64zm0 64H224v96H64V320zm224 96V320H448v96H288zm0-160H448v96H288V256zM64 96h384c35.3 0 64 28.7 64 64v288c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V160c0-35.3 28.7-64 64-64z",
    })
  );
  var gearIcon = h(
    "svg",
    { width: 20, height: 20, viewBox: "0 0 512 512", fill: "currentColor" },
    h("path", {
      d: "M495.9 166.6c3.2 8.7 .5 18.4-6.4 24.6l-43.3 39.4c1.1 8.3 1.7 16.8 1.7 25.4s-.6 17.1-1.7 25.4l43.3 39.4c6.9 6.2 9.6 15.9 6.4 24.6c-4.4 11.9-9.7 23.3-15.8 34.3l-4.7 8.1c-6.6 11-14 21.4-22.1 31.2c-5.9 7.2-15.7 9.6-24.5 6.8l-55.7-17.7c-13.4 10.3-28.2 18.9-44 25.4l-12.5 57.1c-2 9.1-9 16.3-18.2 17.8c-13.8 2.3-28 3.5-42.5 3.5s-28.7-1.2-42.5-3.5c-9.2-1.5-16.2-8.7-18.2-17.8l-12.5-57.1c-15.8-6.5-30.6-15.1-44-25.4L83.1 425.9c-8.8 2.8-18.6 .3-24.5-6.8c-8.1-9.8-15.5-20.2-22.1-31.2l-4.7-8.1c-6.1-11-11.4-22.4-15.8-34.3c-3.2-8.7-.5-18.4 6.4-24.6l43.3-39.4C64.6 273.1 64 264.6 64 256s.6-17.1 1.7-25.4L22.4 191.2c-6.9-6.2-9.6-15.9-6.4-24.6c4.4-11.9 9.7-23.3 15.8-34.3l4.7-8.1c6.6-11 14-21.4 22.1-31.2c5.9-7.2 15.7-9.6 24.5-6.8l55.7 17.7c13.4-10.3 28.2-18.9 44-25.4l12.5-57.1c2-9.1 9-16.3 18.2-17.8C227.3 1.2 241.5 0 256 0s28.7 1.2 42.5 3.5c9.2 1.5 16.2 8.7 18.2 17.8l12.5 57.1c15.8 6.5 30.6 15.1 44 25.4l55.7-17.7c8.8-2.8 18.6-.3 24.5 6.8c8.1 9.8 15.5 20.2 22.1 31.2l4.7 8.1c6.1 11 11.4 22.4 15.8 34.3zM256 336a80 80 0 100-160 80 80 0 000 160z",
    })
  );

  // ── Sidebar Navigation ─────────────────────────────────────────────────
  var panels = [
    { id: "dashboard", title: "Dashboard", icon: chartIcon },
    { id: "data", title: "Data", icon: tableIcon },
    { id: "settings", title: "Settings", icon: gearIcon },
  ];

  // ── Dashboard Panel (registered) ───────────────────────────────────────
  function DashboardPanel(args) {
    var props = args.element.props;
    var monthsResult = useShinyInput(props.months_id, 6);
    var months = monthsResult[0];
    var setMonths = monthsResult[1];

    var regionResult = useShinyInput(props.region_id, "North");
    var region = regionResult[0];
    var setRegion = regionResult[1];

    var regions = ["North", "South", "East", "West"];

    return h(
      "div",
      { className: "panel-content" },
      // Sales Overview Card
      h(
        "div",
        { className: "card" },
        h("div", { className: "card-header" }, "Sales Overview"),
        h(
          "div",
          { className: "card-body" },
          h(ImageOutput, { id: props.sales_plot_id, width: "100%", height: "300px" })
        )
      ),
      // Controls Card
      h(
        "div",
        { className: "card" },
        h("div", { className: "card-header" }, "Controls"),
        h(
          "div",
          { className: "card-body" },
          // Months slider
          h(
            "div",
            { className: "form-group" },
            h(
              "label",
              { htmlFor: "months-slider" },
              "Months: ",
              h("strong", null, months)
            ),
            h("input", {
              id: "months-slider",
              type: "range",
              min: 1,
              max: 12,
              value: months,
              onChange: function (e) {
                setMonths(parseInt(e.target.value, 10));
              },
              className: "form-range",
            })
          ),
          // Region select
          h(
            "div",
            { className: "form-group" },
            h("label", { htmlFor: "region-select" }, "Region:"),
            h(
              "select",
              {
                id: "region-select",
                value: region,
                onChange: function (e) {
                  setRegion(e.target.value);
                },
                className: "form-select",
              },
              regions.map(function (r) {
                return h("option", { key: r, value: r }, r);
              })
            )
          )
        )
      )
    );
  }

  // ── Data Panel (registered) ────────────────────────────────────────────
  function DataPanel(args) {
    var props = args.element.props;
    var tableResult = useShinyOutput(props.data_table_id, undefined);
    var tableData = tableResult[0];

    var refreshResult = useShinyInput(props.refresh_id, 0);
    var refreshCount = refreshResult[0];
    var setRefreshCount = refreshResult[1];

    var refreshCountResult = useShinyOutput(props.refresh_count_id, undefined);
    var refreshText = refreshCountResult[0];

    function handleRefresh() {
      setRefreshCount(refreshCount + 1);
    }

    var tableEl = null;
    if (tableData) {
      var headerCells = [h("th", { key: "name" }, "")].concat(
        tableData.columns.map(function (col) {
          return h("th", { key: col }, col);
        })
      );
      var rows = tableData.rows.map(function (row) {
        return h(
          "tr",
          { key: row.name },
          h("td", { className: "row-name" }, row.name),
          row.values.map(function (val, i) {
            return h("td", { key: i }, typeof val === "number" ? val.toFixed(2) : val);
          })
        );
      });
      tableEl = h(
        "table",
        { className: "data-table" },
        h("thead", null, h("tr", null, headerCells)),
        h("tbody", null, rows)
      );
    }

    return h(
      "div",
      { className: "panel-content" },
      // Data Table Card
      h(
        "div",
        { className: "card" },
        h("div", { className: "card-header" }, "Data Table"),
        h(
          "div",
          { className: "card-body" },
          tableEl || h("div", { className: "loading" }, "Loading...")
        )
      ),
      // Refresh Controls
      h(
        "button",
        {
          className: "btn btn-primary",
          onClick: handleRefresh,
        },
        "Refresh Data"
      ),
      h(
        "pre",
        { className: "refresh-count" },
        refreshText != null ? refreshText : ""
      )
    );
  }

  // ── Settings Panel (registered) ────────────────────────────────────────
  function SettingsPanel(args) {
    var props = args.element.props;
    var usernameResult = useShinyInput(props.username_id, "");
    var username = usernameResult[0];
    var setUsername = usernameResult[1];

    var darkModeResult = useShinyInput(props.dark_mode_id, false);
    var darkMode = darkModeResult[0];
    var setDarkMode = darkModeResult[1];

    var notificationsResult = useShinyInput(props.notifications_id, true);
    var notifications = notificationsResult[0];
    var setNotifications = notificationsResult[1];

    var settingsResult = useShinyOutput(props.settings_output_id, undefined);
    var settingsText = settingsResult[0];

    return h(
      "div",
      { className: "panel-content" },
      // Preferences Card
      h(
        "div",
        { className: "card" },
        h("div", { className: "card-header" }, "Preferences"),
        h(
          "div",
          { className: "card-body" },
          // Username
          h(
            "div",
            { className: "form-group" },
            h("label", { htmlFor: "username-input" }, "Username:"),
            h("input", {
              id: "username-input",
              type: "text",
              value: username,
              onChange: function (e) {
                setUsername(e.target.value);
              },
              className: "form-control",
              placeholder: "Enter username",
            })
          ),
          // Dark Mode
          h(
            "div",
            { className: "form-check" },
            h("input", {
              id: "darkMode-check",
              type: "checkbox",
              checked: darkMode,
              onChange: function (e) {
                setDarkMode(e.target.checked);
              },
              className: "form-check-input",
            }),
            h(
              "label",
              { htmlFor: "darkMode-check", className: "form-check-label" },
              "Dark Mode"
            )
          ),
          // Notifications
          h(
            "div",
            { className: "form-check" },
            h("input", {
              id: "notifications-check",
              type: "checkbox",
              checked: notifications,
              onChange: function (e) {
                setNotifications(e.target.checked);
              },
              className: "form-check-input",
            }),
            h(
              "label",
              {
                htmlFor: "notifications-check",
                className: "form-check-label",
              },
              "Enable Notifications"
            )
          )
        )
      ),
      // Current Settings Card
      h(
        "div",
        { className: "card" },
        h("div", { className: "card-header" }, "Current Settings"),
        h(
          "div",
          { className: "card-body" },
          h(
            "pre",
            { className: "settings-display" },
            settingsText != null ? settingsText : ""
          )
        )
      )
    );
  }

  // ── Main App Component ─────────────────────────────────────────────────
  function SidebarApp(args) {
    var appProps = args.element.props;
    var activePanelState = useState("dashboard");
    var activePanel = activePanelState[0];
    var setActivePanel = activePanelState[1];
    var isOpenState = useState(true);
    var isOpen = isOpenState[0];
    var setIsOpen = isOpenState[1];

    // Chevron icons for collapse button
    var leftChevron = h(
      "svg",
      { width: 20, height: 20, viewBox: "0 0 20 20", fill: "currentColor" },
      h("path", {
        d: "M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z",
      })
    );
    var rightChevron = h(
      "svg",
      { width: 20, height: 20, viewBox: "0 0 20 20", fill: "currentColor" },
      h("path", {
        d: "M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z",
      })
    );

    // Build sidebar nav items
    var navItems = panels.map(function (panel) {
      return h(
        "button",
        {
          key: panel.id,
          className:
            "sidebar-nav-item" +
            (activePanel === panel.id ? " active" : ""),
          onClick: function () {
            setActivePanel(panel.id);
          },
          title: !isOpen ? panel.title : undefined,
        },
        h("span", { className: "sidebar-nav-icon" }, panel.icon),
        isOpen ? h("span", { className: "sidebar-nav-label" }, panel.title) : null
      );
    });

    // Render the active panel — children are spec-driven panel components
    var childArray = React.Children.toArray(args.children);
    var activeIndex = panels.findIndex(function (p) { return p.id === activePanel; });
    var panelContent = childArray[activeIndex] || null;

    return h(
      "div",
      {
        className: "sidebar-layout",
        "data-open": isOpen ? "true" : "false",
      },
      // Sidebar
      h(
        "aside",
        {
          className: "sidebar",
          style: { width: isOpen ? "250px" : "60px" },
        },
        // Header
        h(
          "div",
          { className: "sidebar-header" },
          isOpen ? h("span", { className: "sidebar-title" }, appProps.title) : null,
          h(
            "button",
            {
              className: "sidebar-collapse-btn",
              onClick: function () {
                setIsOpen(!isOpen);
              },
              "aria-label": isOpen ? "Collapse sidebar" : "Expand sidebar",
            },
            isOpen ? leftChevron : rightChevron
          )
        ),
        // Nav
        h("nav", { className: "sidebar-nav" }, navItems)
      ),
      // Main content
      h("main", { className: "sidebar-content" }, panelContent)
    );
  }

  window.shinyjson.registerComponents(null, {
    SidebarApp: SidebarApp,
    DashboardPanel: DashboardPanel,
    DataPanel: DataPanel,
    SettingsPanel: SettingsPanel,
  });
})();
