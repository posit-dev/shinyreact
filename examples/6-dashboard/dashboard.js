// Dashboard — shinyjson conversion of shiny-react-upstream/6-dashboard
// Registers App, Sidebar, FilterPanel, MetricsCards, Charts, DataTable components.
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useState = React.useState;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyOutput = window.shinyjson.useShinyOutput;

  // ---------------------------------------------------------------------------
  // Utility helpers
  // ---------------------------------------------------------------------------

  function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  // ---------------------------------------------------------------------------
  // FilterPanel
  // ---------------------------------------------------------------------------

  function FilterPanel(args) {
    var props = args.element.props;
    var dateRangeResult = useShinyInput(props.date_range_id, "last_30_days");
    var dateRange = dateRangeResult[0];
    var setDateRange = dateRangeResult[1];

    var searchResult = useShinyInput(props.search_id, "");
    var searchTerm = searchResult[0];
    var setSearchTerm = searchResult[1];

    var catResult = useShinyInput(props.categories_id, []);
    var selectedCategories = catResult[0];
    var setSelectedCategories = catResult[1];

    var dateRangeOptions = [
      { value: "last_7_days", label: "Last 7 days" },
      { value: "last_30_days", label: "Last 30 days" },
      { value: "last_90_days", label: "Last 90 days" },
      { value: "this_year", label: "This year" },
    ];

    var categoryOptions = [
      { value: "electronics", label: "Electronics" },
      { value: "clothing", label: "Clothing" },
      { value: "books", label: "Books" },
      { value: "home", label: "Home & Garden" },
      { value: "sports", label: "Sports" },
    ];

    function toggleCategory(cat) {
      if (selectedCategories.indexOf(cat) >= 0) {
        setSelectedCategories(selectedCategories.filter(function (c) { return c !== cat; }));
      } else {
        setSelectedCategories(selectedCategories.concat([cat]));
      }
    }

    return h("div", { className: "filter-panel" },
      // Search
      h("div", { className: "filter-section" },
        h("label", { className: "filter-label" }, "Search"),
        h("div", { className: "search-box" },
          h("input", {
            type: "text",
            value: searchTerm,
            onChange: function (e) { setSearchTerm(e.target.value); },
            placeholder: "Search products...",
            className: "search-input",
          }),
          searchTerm ? h("button", {
            className: "clear-btn",
            onClick: function () { setSearchTerm(""); },
          }, "\u00D7") : null
        )
      ),

      // Date range
      h("div", { className: "filter-section" },
        h("label", { className: "filter-label" }, "Time Period"),
        h("div", { className: "date-range-buttons" },
          dateRangeOptions.map(function (opt) {
            return h("button", {
              key: opt.value,
              className: "date-btn" + (dateRange === opt.value ? " active" : ""),
              onClick: function () { setDateRange(opt.value); },
            }, opt.label);
          })
        )
      ),

      // Categories
      h("div", { className: "filter-section" },
        h("label", { className: "filter-label" }, "Categories"),
        h("div", { className: "category-badges" },
          categoryOptions.map(function (cat) {
            var isSelected = selectedCategories.indexOf(cat.value) >= 0;
            return h("button", {
              key: cat.value,
              className: "badge" + (isSelected ? " badge-active" : ""),
              onClick: function () { toggleCategory(cat.value); },
            }, cat.label, isSelected ? " \u00D7" : "");
          })
        )
      ),

      // Active filters summary
      (searchTerm || selectedCategories.length > 0)
        ? h("div", { className: "active-filters" },
            h("label", { className: "filter-label" }, "Active Filters"),
            h("div", { className: "category-badges" },
              searchTerm ? h("span", { className: "badge badge-secondary" }, "Search: " + searchTerm) : null,
              selectedCategories.map(function (cat) {
                var label = categoryOptions.find(function (c) { return c.value === cat; });
                return h("span", { key: cat, className: "badge badge-secondary" }, label ? label.label : cat);
              })
            )
          )
        : null
    );
  }

  // ---------------------------------------------------------------------------
  // Sidebar
  // ---------------------------------------------------------------------------

  var NAV_ITEMS = ["Dashboard", "Analytics", "Customers", "Orders", "Performance"];
  var SECONDARY_ITEMS = ["Settings", "Help"];

  function Sidebar(props) {
    var activePage = props.activePage;
    var onNavigate = props.onNavigate;

    return h("aside", { className: "sidebar" },
      h("div", { className: "sidebar-header" },
        h("h2", null, "Analytics Dashboard")
      ),
      h("nav", { className: "sidebar-nav" },
        NAV_ITEMS.map(function (title) {
          return h("a", {
            key: title,
            href: "#",
            className: "nav-item" + (activePage === title ? " active" : ""),
            onClick: function (e) { e.preventDefault(); onNavigate(title); },
          }, title);
        })
      ),
      h("hr", { className: "sidebar-divider" }),
      h("nav", { className: "sidebar-nav" },
        SECONDARY_ITEMS.map(function (title) {
          return h("a", {
            key: title,
            href: "#",
            className: "nav-item" + (activePage === title ? " active" : ""),
            onClick: function (e) { e.preventDefault(); onNavigate(title); },
          }, title);
        })
      ),
      h("hr", { className: "sidebar-divider" }),
      props.filterPanel
    );
  }

  // ---------------------------------------------------------------------------
  // MetricsCards
  // ---------------------------------------------------------------------------

  function MetricsCards(args) {
    var result = useShinyOutput(args.element.props.output_id, undefined);
    var metricsData = result[0];
    var isLoading = result[1];

    if (!metricsData || isLoading) {
      return h("div", { className: "metrics-grid" },
        [0, 1, 2, 3].map(function (i) {
          return h("div", { key: i, className: "card metric-card skeleton-card" },
            h("div", { className: "skeleton skeleton-title" }),
            h("div", { className: "skeleton skeleton-value" }),
            h("div", { className: "skeleton skeleton-change" })
          );
        })
      );
    }

    var metricKeys = ["revenue", "users", "orders", "conversion"];
    var icons = {
      revenue: "$",
      users: "\uD83D\uDC64",
      orders: "\uD83D\uDED2",
      conversion: "\u26A1",
    };

    return h("div", { className: "metrics-grid" },
      metricKeys.map(function (key) {
        var m = metricsData[key];
        return h("div", { key: key, className: "card metric-card" },
          h("div", { className: "metric-header" },
            h("span", { className: "metric-title" }, m.title),
            h("span", { className: "metric-icon" }, icons[key])
          ),
          h("div", { className: "metric-value" }, m.value),
          h("div", { className: "metric-change" },
            h("span", {
              className: "change-badge " + (m.trend === "up" ? "up" : "down"),
            }, (m.trend === "up" ? "\u2191 " : "\u2193 ") + Math.abs(m.change) + "%"),
            h("span", { className: "change-label" }, " from last month")
          )
        );
      })
    );
  }

  // ---------------------------------------------------------------------------
  // Charts (CSS bar charts — no recharts available)
  // ---------------------------------------------------------------------------

  function Charts(args) {
    var result = useShinyOutput(args.element.props.output_id, undefined);
    var chartColumnsData = result[0];
    var isLoading = result[1];

    if (!chartColumnsData || isLoading) {
      return h("div", { className: "charts-container" },
        h("div", { className: "card chart-card" },
          h("div", { className: "card-header" }, "Revenue Trend"),
          h("div", { className: "skeleton skeleton-chart" })
        ),
        h("div", { className: "card chart-card" },
          h("div", { className: "card-header" }, "Category Performance"),
          h("div", { className: "skeleton skeleton-chart" })
        )
      );
    }

    // Convert column-major to row-major
    var revenueTrend = [];
    var dates = chartColumnsData.revenue_trend.date || [];
    for (var i = 0; i < dates.length; i++) {
      revenueTrend.push({
        date: dates[i],
        revenue: chartColumnsData.revenue_trend.revenue[i] || 0,
        orders: chartColumnsData.revenue_trend.orders[i] || 0,
      });
    }

    var categoryPerf = [];
    var cats = chartColumnsData.category_performance.category || [];
    for (var j = 0; j < cats.length; j++) {
      categoryPerf.push({
        category: cats[j],
        revenue: chartColumnsData.category_performance.revenue[j] || 0,
        sales: chartColumnsData.category_performance.sales[j] || 0,
      });
    }

    // For revenue trend, sample down to ~15 points for display
    var step = Math.max(1, Math.floor(revenueTrend.length / 15));
    var sampledRevenue = revenueTrend.filter(function (_, idx) { return idx % step === 0; });
    var maxRevenue = Math.max.apply(null, sampledRevenue.map(function (d) { return d.revenue; }));

    // For category performance
    var maxCatRevenue = Math.max.apply(null, categoryPerf.map(function (d) { return d.revenue; }));

    return h("div", { className: "charts-container" },
      // Revenue Trend (vertical bars)
      h("div", { className: "card chart-card" },
        h("div", { className: "card-header" }, "\u2197 Revenue Trend"),
        h("div", { className: "bar-chart" },
          sampledRevenue.map(function (d, idx) {
            var pct = maxRevenue > 0 ? (d.revenue / maxRevenue) * 100 : 0;
            return h("div", { key: idx, className: "bar-col", title: formatDate(d.date) + ": " + formatCurrency(d.revenue) },
              h("div", { className: "bar-fill", style: { height: pct + "%" } }),
              h("div", { className: "bar-label" }, formatDate(d.date))
            );
          })
        )
      ),

      // Category Performance (horizontal bars)
      h("div", { className: "card chart-card" },
        h("div", { className: "card-header" }, "\u2593 Category Performance"),
        h("div", { className: "h-bar-chart" },
          categoryPerf.map(function (d) {
            var pct = maxCatRevenue > 0 ? (d.revenue / maxCatRevenue) * 100 : 0;
            return h("div", { key: d.category, className: "h-bar-row" },
              h("div", { className: "h-bar-label" }, d.category),
              h("div", { className: "h-bar-track" },
                h("div", { className: "h-bar-fill", style: { width: pct + "%" } })
              ),
              h("div", { className: "h-bar-value" }, formatCurrency(d.revenue))
            );
          })
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // DataTable
  // ---------------------------------------------------------------------------

  function DataTable(args) {
    var result = useShinyOutput(args.element.props.output_id, undefined);
    var tableData = result[0];
    var isLoading = result[1];

    if (!tableData || isLoading) {
      return h("div", { className: "card table-card" },
        h("div", { className: "card-header" }, "Top Products"),
        h("div", { className: "skeleton-rows" },
          [0, 1, 2, 3, 4].map(function (i) {
            return h("div", { key: i, className: "skeleton skeleton-row" });
          })
        )
      );
    }

    var cols = tableData.columns;
    var numRows = cols.id ? cols.id.length : 0;

    function getStatusClass(status) {
      if (status === "active") return "status-active";
      if (status === "low_stock") return "status-low-stock";
      return "status-inactive";
    }

    function getStatusLabel(status) {
      if (status === "active") return "Active";
      if (status === "low_stock") return "Low Stock";
      if (status === "inactive") return "Inactive";
      return status;
    }

    var rows = [];
    for (var i = 0; i < numRows; i++) {
      rows.push(i);
    }

    return h("div", { className: "card table-card" },
      h("div", { className: "card-header" }, "Top Products"),
      h("div", { className: "table-wrapper" },
        h("table", { className: "data-table" },
          h("thead", null,
            h("tr", null,
              h("th", null, "Product"),
              h("th", null, "Category"),
              h("th", { className: "text-right" }, "Sales"),
              h("th", { className: "text-right" }, "Revenue"),
              h("th", { className: "text-right" }, "Growth"),
              h("th", null, "Status")
            )
          ),
          h("tbody", null,
            rows.map(function (i) {
              var growth = cols.growth[i] || 0;
              var growthStr = (growth >= 0 ? "+" : "") + growth.toFixed(1) + "%";
              return h("tr", { key: cols.id[i] },
                h("td", { className: "font-medium" }, cols.product[i]),
                h("td", null, h("span", { className: "badge badge-outline" }, cols.category[i])),
                h("td", { className: "text-right" }, (cols.sales[i] || 0).toLocaleString()),
                h("td", { className: "text-right" }, formatCurrency(cols.revenue[i] || 0)),
                h("td", { className: "text-right" },
                  h("span", { className: growth >= 0 ? "text-green" : "text-red" }, growthStr)
                ),
                h("td", null,
                  h("span", { className: "status-badge " + getStatusClass(cols.status[i]) },
                    getStatusLabel(cols.status[i])
                  )
                )
              );
            })
          )
        )
      ),
      tableData.total_rows > numRows
        ? h("div", { className: "table-footer" },
            "Showing " + numRows + " of " + tableData.total_rows + " products"
          )
        : null
    );
  }

  // ---------------------------------------------------------------------------
  // App (top-level layout)
  // ---------------------------------------------------------------------------

  function PlaceholderPage(props) {
    return h("main", { className: "main-content" },
      h("div", { className: "page-header" },
        h("h1", null, props.title),
        h("p", null, props.title + " page content goes here.")
      )
    );
  }

  function DashboardPage(props) {
    // props.metricsCards, props.charts, props.dataTable are rendered children
    return h("main", { className: "main-content" },
      h("div", { className: "page-header" },
        h("h1", null, "Dashboard"),
        h("p", null, "Welcome to your analytics dashboard. Monitor your key metrics and performance.")
      ),
      h("hr", { className: "separator" }),
      props.metricsCards,
      h("div", { className: "content-grid" },
        props.charts,
        props.dataTable
      )
    );
  }

  function DashboardApp(args) {
    var pageState = useState("Dashboard");
    var activePage = pageState[0];
    var setActivePage = pageState[1];

    // Children order: FilterPanel, MetricsCards, Charts, DataTable
    var childArray = React.Children.toArray(args.children);
    var filterPanel = childArray[0];
    var metricsCards = childArray[1];
    var charts = childArray[2];
    var dataTable = childArray[3];

    var content;
    if (activePage === "Dashboard") {
      content = h(DashboardPage, { metricsCards: metricsCards, charts: charts, dataTable: dataTable });
    } else {
      content = h(PlaceholderPage, { title: activePage });
    }

    return h("div", { className: "dashboard-layout" },
      h(Sidebar, { activePage: activePage, onNavigate: setActivePage, filterPanel: filterPanel }),
      content
    );
  }

  // ---------------------------------------------------------------------------
  // Register all components with shinyjson
  // ---------------------------------------------------------------------------

  window.shinyjson.registerComponents(null, {
    DashboardApp: DashboardApp,
    FilterPanel: FilterPanel,
    MetricsCards: MetricsCards,
    Charts: Charts,
    DataTable: DataTable,
  });
})();
