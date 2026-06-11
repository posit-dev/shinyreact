import * as React from "react";
import * as RechartsPrimitive from "recharts";
import { cn } from "@/lib/utils";
const THEMES = { light: "", dark: ".dark" };
const INITIAL_DIMENSION = { width: 320, height: 200 };
const ChartContext = React.createContext(null);
function useChart() {
  const context = React.useContext(ChartContext);
  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />");
  }
  return context;
}
function ChartContainer({
  id,
  className,
  children,
  config,
  initialDimension = INITIAL_DIMENSION,
  ...props
}) {
  const uniqueId = React.useId();
  const chartId = `chart-${id ?? uniqueId.replace(/:/g, "")}`;
  return <ChartContext.Provider value={{ config }}><div
    data-slot="chart"
    data-chart={chartId}
    className={cn(
      "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-hidden [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector]:outline-hidden [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-surface]:outline-hidden",
      className
    )}
    {...props}
  ><ChartStyle id={chartId} config={config} /><RechartsPrimitive.ResponsiveContainer
    initialDimension={initialDimension}
  >{children}</RechartsPrimitive.ResponsiveContainer></div></ChartContext.Provider>;
}
const ChartStyle = ({ id, config }) => {
  const colorConfig = Object.entries(config).filter(
    ([, config2]) => config2.theme ?? config2.color
  );
  if (!colorConfig.length) {
    return null;
  }
  return <style
    dangerouslySetInnerHTML={{
      __html: Object.entries(THEMES).map(
        ([theme, prefix]) => `
${prefix} [data-chart=${id}] {
${colorConfig.map(([key, itemConfig]) => {
          const color = itemConfig.theme?.[theme] ?? itemConfig.color;
          return color ? `  --color-${key}: ${color};` : null;
        }).join("\n")}
}
`
      ).join("\n")
    }}
  />;
};
const ChartTooltip = RechartsPrimitive.Tooltip;
function ChartTooltipContent({
  active,
  payload,
  className,
  indicator = "dot",
  hideLabel = false,
  hideIndicator = false,
  label,
  labelFormatter,
  labelClassName,
  formatter,
  color,
  nameKey,
  labelKey
}) {
  const { config } = useChart();
  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || !payload?.length) {
      return null;
    }
    const [item] = payload;
    const key = `${labelKey ?? item?.dataKey ?? item?.name ?? "value"}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    const value = !labelKey && typeof label === "string" ? config[label]?.label ?? label : itemConfig?.label;
    if (labelFormatter) {
      return <div className={cn("font-medium", labelClassName)}>{labelFormatter(value, payload)}</div>;
    }
    if (!value) {
      return null;
    }
    return <div className={cn("font-medium", labelClassName)}>{value}</div>;
  }, [
    label,
    labelFormatter,
    payload,
    hideLabel,
    labelClassName,
    config,
    labelKey
  ]);
  if (!active || !payload?.length) {
    return null;
  }
  const nestLabel = payload.length === 1 && indicator !== "dot";
  return <div
    className={cn(
      "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
      className
    )}
  >{!nestLabel ? tooltipLabel : null}<div className="grid gap-1.5">{payload.filter((item) => item.type !== "none").map((item, index) => {
    const key = `${nameKey ?? item.name ?? item.dataKey ?? "value"}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    const indicatorColor = color ?? item.payload?.fill ?? item.color;
    return <div
      key={index}
      className={cn(
        "flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground",
        indicator === "dot" && "items-center"
      )}
    >{formatter && item?.value !== void 0 && item.name ? formatter(item.value, item.name, item, index, item.payload) : <>{itemConfig?.icon ? <itemConfig.icon /> : !hideIndicator && <div
      className={cn(
        "shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg)",
        {
          "h-2.5 w-2.5": indicator === "dot",
          "w-1": indicator === "line",
          "w-0 border-[1.5px] border-dashed bg-transparent": indicator === "dashed",
          "my-0.5": nestLabel && indicator === "dashed"
        }
      )}
      style={{
        "--color-bg": indicatorColor,
        "--color-border": indicatorColor
      }}
    />}<div
      className={cn(
        "flex flex-1 justify-between leading-none",
        nestLabel ? "items-end" : "items-center"
      )}
    ><div className="grid gap-1.5">{nestLabel ? tooltipLabel : null}<span className="text-muted-foreground">{itemConfig?.label ?? item.name}</span></div>{item.value != null && <span className="font-mono font-medium text-foreground tabular-nums">{typeof item.value === "number" ? item.value.toLocaleString() : String(item.value)}</span>}</div></>}</div>;
  })}</div></div>;
}
const ChartLegend = RechartsPrimitive.Legend;
function ChartLegendContent({
  className,
  hideIcon = false,
  payload,
  verticalAlign = "bottom",
  nameKey
}) {
  const { config } = useChart();
  if (!payload?.length) {
    return null;
  }
  return <div
    className={cn(
      "flex items-center justify-center gap-4",
      verticalAlign === "top" ? "pb-3" : "pt-3",
      className
    )}
  >{payload.filter((item) => item.type !== "none").map((item, index) => {
    const key = `${nameKey ?? item.dataKey ?? "value"}`;
    const itemConfig = getPayloadConfigFromPayload(config, item, key);
    return <div
      key={index}
      className={cn(
        "flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground"
      )}
    >{itemConfig?.icon && !hideIcon ? <itemConfig.icon /> : <div
      className="h-2 w-2 shrink-0 rounded-[2px]"
      style={{
        backgroundColor: item.color
      }}
    />}{itemConfig?.label}</div>;
  })}</div>;
}
function getPayloadConfigFromPayload(config, payload, key) {
  if (typeof payload !== "object" || payload === null) {
    return void 0;
  }
  const payloadPayload = "payload" in payload && typeof payload.payload === "object" && payload.payload !== null ? payload.payload : void 0;
  let configLabelKey = key;
  if (key in payload && typeof payload[key] === "string") {
    configLabelKey = payload[key];
  } else if (payloadPayload && key in payloadPayload && typeof payloadPayload[key] === "string") {
    configLabelKey = payloadPayload[key];
  }
  return configLabelKey in config ? config[configLabelKey] : config[key];
}

// Default palette when series don't specify colors.
const PALETTE = [
  "hsl(221, 83%, 53%)",
  "hsl(142, 71%, 45%)",
  "hsl(38, 92%, 50%)",
  "hsl(0, 84%, 60%)",
  "hsl(258, 90%, 66%)",
];

// --- shinyreact bridge ---
// Display: no hook. Data-driven recharts wrapper.
// Props:
//   type    "bar" | "line" | "area" | "pie"  (default "bar")
//   data    [{x_key: label, series_key: value, ...}, ...]
//   series  [{key, label?, color?}, ...]  — which keys to plot
//   x_key   key used as x-axis / pie name (default "name")
//   height  px height (default 300)
//   legend  show legend (default true)
//   grid    show cartesian grid (default true)
//   className
function ShinyChart({ element }) {
  const {
    type = "bar",
    data = [],
    series = [],
    x_key = "name",
    height = 300,
    legend = true,
    grid = true,
    className,
  } = element.props;

  // Build ChartContainer config: {key: {label, color}}
  const config = Object.fromEntries(
    series.map(({ key, label, color }, i) => [
      key,
      { label: label ?? key, color: color ?? PALETTE[i % PALETTE.length] },
    ])
  );

  const cartesianSeries = () =>
    series.map(({ key }, i) => {
      const fill = `var(--color-${key})`;
      if (type === "bar")
        return <RechartsPrimitive.Bar key={key} dataKey={key} fill={fill} radius={4} />;
      if (type === "area")
        return <RechartsPrimitive.Area key={key} type="monotone" dataKey={key} stroke={fill} fill={fill} fillOpacity={0.15} strokeWidth={2} />;
      return <RechartsPrimitive.Line key={key} type="monotone" dataKey={key} stroke={fill} strokeWidth={2} dot={false} />;
    });

  if (type === "pie") {
    const pieData = data.map((row, i) => ({
      ...row,
      fill: series[0]?.color ?? PALETTE[i % PALETTE.length],
    }));
    return (
      <ChartContainer config={config} className={className} style={{ height }}>
        <RechartsPrimitive.PieChart>
          <ChartTooltip content={<ChartTooltipContent nameKey={x_key} />} />
          {legend && <ChartLegend content={<ChartLegendContent />} />}
          <RechartsPrimitive.Pie
            data={pieData}
            dataKey={series[0]?.key ?? "value"}
            nameKey={x_key}
            strokeWidth={2}
          />
        </RechartsPrimitive.PieChart>
      </ChartContainer>
    );
  }

  const ChartRoot = type === "area"
    ? RechartsPrimitive.AreaChart
    : type === "line"
      ? RechartsPrimitive.LineChart
      : RechartsPrimitive.BarChart;

  return (
    <ChartContainer config={config} className={className} style={{ height }}>
      <ChartRoot data={data}>
        {grid && <RechartsPrimitive.CartesianGrid vertical={false} />}
        <RechartsPrimitive.XAxis
          dataKey={x_key}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <RechartsPrimitive.YAxis tickLine={false} axisLine={false} tickMargin={8} />
        <ChartTooltip content={<ChartTooltipContent />} />
        {legend && <ChartLegend content={<ChartLegendContent />} />}
        {cartesianSeries()}
      </ChartRoot>
    </ChartContainer>
  );
}

export { ShinyChart as Chart };
