# Interactive Dashboard Example

This example demonstrates a modern, interactive analytics dashboard built with **shiny-react** and **shadcn/ui**. It showcases advanced patterns for building production-quality applications with React frontends and Shiny backends.

## Features

- 🎨 **Modern UI**: Built with shadcn/ui and Tailwind CSS
- 📊 **Interactive Charts**: Real-time data visualization with Recharts
- 📋 **Data Tables**: Sortable, filterable product performance tables
- 🔍 **Advanced Filtering**: Date ranges, search, and multi-category filters
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- ⚡ **Real-time Updates**: Live data synchronization between React and Shiny
- 🌙 **Dark Mode Ready**: Full dark/light theme support
- 🏗️ **Component Architecture**: Reusable, modular component design

## What This Example Demonstrates

### UI/UX Patterns
- **Dashboard Layout**: Professional sidebar navigation with main content area
- **Metric Cards**: KPI displays with trend indicators and change percentages
- **Interactive Filters**: Complex multi-input filtering with real-time updates
- **Data Tables**: Advanced table with sorting, status badges, and formatting
- **Charts**: Multiple chart types (line charts, bar charts) with tooltips
- **Loading States**: Skeleton loading indicators during data fetching

### shiny-react Integration
- **Complex State Management**: Multiple coordinated inputs and outputs
- **Real-time Filtering**: Server-side data processing based on React filters
- **Custom Renderers**: Both R and Python backends with custom JSON outputs
- **Performance Optimization**: Debounced inputs and efficient data updates
- **Type Safety**: Full TypeScript types for all data structures

### Technical Architecture
- **Component Composition**: Hierarchical component structure with clear separation
- **Utility Functions**: Shared utilities for formatting, styling, and data processing
- **Build System**: Tailwind CSS processing with PostCSS
- **Dual Backends**: Identical functionality in both R and Python

## Directory Structure

```
5-dashboard/
├── package.json             # Dependencies and build scripts
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── postcss.config.js        # PostCSS configuration
├── components.json          # shadcn/ui configuration
├── srcts/                   # React TypeScript source
│   ├── main.tsx             # Application entry point
│   ├── globals.css          # Global styles and CSS variables
│   ├── lib/
│   │   └── utils.ts         # Utility functions (cn helper)
│   └── components/
│       ├── ui/              # shadcn/ui base components
│       │   ├── card.tsx
│       │   ├── button.tsx
│       │   ├── badge.tsx
│       │   ├── input.tsx
│       │   ├── table.tsx
│       │   ├── skeleton.tsx
│       │   └── separator.tsx
│       ├── Dashboard.tsx    # Main dashboard container
│       ├── Sidebar.tsx      # Navigation sidebar
│       ├── MetricsCards.tsx # KPI metric displays
│       ├── FilterPanel.tsx  # Advanced filtering controls
│       ├── DataTable.tsx    # Interactive data table
│       └── Charts.tsx       # Chart visualizations
├── r/                       # R Shiny backend
│   ├── app.R                # Main R application
│   ├── shinyreact.R         # R functions for shiny-react
│   └── www/                 # Built assets (auto-generated)
└── py/                      # Python Shiny backend
    ├── app.py               # Main Python application
    ├── shinyreact.py        # Python functions for shiny-react
    └── www/                 # Built assets (auto-generated)
```

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Build the Frontend

```bash
# Build once
npm run build

# Or watch for changes during development
npm run watch
```

### 3. Run the Shiny Server

**Option A: R Backend**
```bash
R -e "options(shiny.autoreload = TRUE); shiny::runApp('r/app.R', port=8000)"
```

**Option B: Python Backend**
```bash
# Install Python dependencies first
pip install shiny pandas numpy

# Run the server
shiny run py/app.py --port 8000 --reload
```

### 4. Open Your Browser

Navigate to `http://localhost:8000` to see the dashboard.

## Key Components

### MetricsCards
Displays key performance indicators with:
- Current values (revenue, users, orders, conversion rate)
- Percentage change from previous period
- Trend indicators (up/down arrows)
- Color-coded badges for positive/negative changes

### FilterPanel
Advanced filtering interface with:
- **Search**: Text search across products and categories
- **Date Range**: Predefined time periods (7 days, 30 days, 90 days, this year)
- **Categories**: Multi-select category filtering with toggle badges
- **Active Filters**: Summary of currently applied filters

### DataTable
Interactive product performance table featuring:
- **Sortable Columns**: Click headers to sort by different metrics
- **Status Badges**: Visual indicators for product status
- **Currency Formatting**: Proper formatting for monetary values
- **Pagination Info**: Shows current vs. total row counts

### Charts
Multiple chart visualizations:
- **Revenue Trend**: Line chart showing revenue over time
- **Category Performance**: Bar chart comparing category sales
- **Interactive Tooltips**: Hover for detailed information
- **Responsive Design**: Automatically adapts to container size

## Data Flow

```
React Filters ──[useShinyInput]──> Shiny Server
                                        │
                                        ▼
                                 Filter & Process Data
                                        │
                                        ▼
                              Generate Metrics, Charts, Table
                                        │
                                        ▼
React Components <──[useShinyOutput]── Shiny Server
```

### Input IDs
- `date_range`: Selected time period ("last_7_days", "last_30_days", etc.)
- `search_term`: Text search query
- `selected_categories`: Array of selected category IDs

### Output IDs
- `metrics_data`: KPI metrics with trends
- `chart_data`: Time series and category performance data
- `table_data`: Top products with pagination info

## Customization

### Adding New Metrics
1. **Backend**: Modify `calculate_metrics()` in `shinyreact.R` or `shinyreact.py`
2. **Frontend**: Update `MetricsCards.tsx` to display new metrics
3. **Types**: Add TypeScript interfaces for new data structures

### Adding New Charts
1. **Backend**: Include chart data in `chart_data` output
2. **Frontend**: Add new chart components in `Charts.tsx`
3. **Styling**: Use recharts components with shadcn/ui styling

### Styling Customization
- **Colors**: Modify CSS variables in `globals.css`
- **Components**: Customize shadcn/ui components in `components/ui/`
- **Layout**: Adjust responsive breakpoints in Tailwind config

## Development Tips

### Hot Reload Setup
Run these commands in separate terminals for the best development experience:

```bash
# Terminal 1: Build watcher
npm run watch

# Terminal 2: Shiny server with auto-reload
R -e "options(shiny.autoreload = TRUE); shiny::runApp('r/app.R', port=8000)"
```

### Debugging
- **React**: Use browser DevTools Console and React DevTools
- **Shiny**: Check R/Python console for server logs
- **Data Flow**: Monitor Network tab for WebSocket communication
- **Performance**: Use React Profiler for component render analysis

### Common Issues
1. **Build Failures**: Ensure all npm dependencies are installed
2. **Styling Issues**: Check that Tailwind CSS is processing correctly
3. **Data Sync**: Verify input/output IDs match between React and Shiny
4. **Type Errors**: Run `tsc --noEmit` to check TypeScript compilation

## Production Considerations

- **Performance**: Implement proper memoization for expensive calculations
- **Security**: Validate and sanitize all user inputs on the server
- **Accessibility**: Add proper ARIA labels and keyboard navigation
- **Error Handling**: Implement robust error boundaries and fallbacks
- **Testing**: Add unit tests for components and integration tests for data flow
- **Monitoring**: Implement logging and performance monitoring

This example serves as a comprehensive template for building sophisticated analytics dashboards with shiny-react and modern React patterns.
