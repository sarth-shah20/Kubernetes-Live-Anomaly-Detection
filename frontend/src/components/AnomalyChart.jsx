import { useMemo } from "react";
import { format } from "date-fns";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const palette = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#f43f5e", "#38bdf8", "#f97316"];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-xl border border-slate-700/80 bg-slate-950/95 p-4 shadow-xl shadow-slate-950/60">
      <p className="mb-3 text-sm font-semibold text-white">{format(new Date(label), "HH:mm:ss")}</p>
      <div className="space-y-2">
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-slate-200">{entry.dataKey}</span>
            </div>
            <span className="font-semibold tabular-nums text-white">
              {entry.value == null ? "—" : Number(entry.value).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AnomalyChart({ scoreHistory }) {
  const { chartData, podNames } = useMemo(() => {
    const trimmed = (scoreHistory ?? []).slice(-50);
    const discoveredPods = Array.from(
      new Set(trimmed.flatMap((entry) => Object.keys(entry.pods ?? {}))),
    );

    const rows = trimmed.map((entry) => {
      const row = { timestamp: entry.timestamp };
      discoveredPods.forEach((podName) => {
        row[podName] = Object.prototype.hasOwnProperty.call(entry.pods ?? {}, podName)
          ? entry.pods[podName]
          : null;
      });
      return row;
    });

    return { chartData: rows, podNames: discoveredPods };
  }, [scoreHistory]);

  return (
    <section className="glass-card p-5 shadow-lg shadow-slate-950/30">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Anomaly Score Timeline</h2>
          <p className="text-sm text-slate-400">The last 50 score snapshots across monitored pods.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
          {podNames.length ? (
            podNames.map((podName, index) => (
              <div key={podName} className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: palette[index % palette.length] }} />
                <span>{podName}</span>
              </div>
            ))
          ) : (
            <span className="text-slate-500">No pod history yet</span>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={chartData}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.14)" strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              minTickGap={24}
              stroke="#94a3b8"
              tickFormatter={(value) => format(new Date(value), "HH:mm:ss")}
            />
            <YAxis
              domain={[0, 1]}
              ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
              stroke="#94a3b8"
              label={{ value: "Anomaly Score", angle: -90, position: "insideLeft", fill: "#cbd5e1" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine
              y={0.6}
              stroke="#ef4444"
              strokeDasharray="6 6"
              label={{ value: "Alert Threshold", fill: "#fca5a5", position: "insideTopRight" }}
            />
            <ReferenceLine
              y={0.8}
              stroke="#f59e0b"
              strokeDasharray="6 6"
              label={{ value: "High Severity", fill: "#fcd34d", position: "insideBottomRight" }}
            />
            {podNames.map((podName, index) => (
              <Line
                key={podName}
                type="monotone"
                dataKey={podName}
                stroke={palette[index % palette.length]}
                strokeWidth={2.5}
                dot={false}
                connectNulls={false}
                isAnimationActive
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
