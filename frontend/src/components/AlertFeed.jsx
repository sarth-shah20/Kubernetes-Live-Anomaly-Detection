import { useMemo, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { AlertTriangle, CheckCircle2, Trash2 } from "lucide-react";

function severityBorder(severity) {
  switch (severity) {
    case "high":
      return "border-red-500";
    case "medium":
      return "border-amber-500";
    case "low":
      return "border-yellow-500";
    default:
      return "border-emerald-500";
  }
}

function severityBadge(severity) {
  switch (severity) {
    case "high":
      return "border-red-500/30 bg-red-500/10 text-red-200";
    case "medium":
      return "border-amber-500/30 bg-amber-500/10 text-amber-200";
    case "low":
      return "border-yellow-500/30 bg-yellow-500/10 text-yellow-200";
    default:
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  }
}

export default function AlertFeed({ alerts }) {
  const [clearedAt, setClearedAt] = useState(null);

  const visibleAlerts = useMemo(() => {
    return [...(alerts ?? [])]
      .filter((alert) => !clearedAt || new Date(alert.timestamp).getTime() > clearedAt)
      .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime());
  }, [alerts, clearedAt]);

  return (
    <section className="glass-card p-5 shadow-lg shadow-slate-950/30">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-white">Live Alert Feed</h2>
          <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-slate-700/70 bg-slate-900/80 px-3 py-1 text-sm text-slate-300">
            <span className="h-2 w-2 rounded-full bg-red-400 animate-pulse-dot" />
            {alerts?.length ?? 0} alerts this session
          </div>
        </div>

        <button
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700/70 bg-slate-900/80 px-3 py-2 text-sm text-slate-200 transition-all duration-300 hover:border-cyan-400 hover:text-cyan-300"
          onClick={() => setClearedAt(Date.now())}
          type="button"
        >
          <Trash2 className="h-4 w-4" />
          Clear
        </button>
      </div>

      {!visibleAlerts.length ? (
        <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-emerald-500/30 bg-emerald-500/5 text-center">
          <CheckCircle2 className="mb-4 h-10 w-10 text-emerald-400" />
          <p className="text-lg font-medium text-white">No anomalies detected in this session</p>
          <p className="mt-2 text-sm text-slate-400">Fresh alerts will slide in here when the model flags a pod.</p>
        </div>
      ) : (
        <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
          {visibleAlerts.map((alert) => (
            <article
              key={`${alert.pod_name}-${alert.timestamp}`}
              className={`animate-slide-in-right rounded-xl border-l-4 ${severityBorder(alert.severity)} bg-slate-900/80 p-4 transition-all duration-300`}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-white">{alert.pod_name}</h3>
                  <p className="text-sm text-slate-400">{alert.namespace}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${severityBadge(alert.severity)}`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-slate-400">
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 text-sm">
                <span className="rounded-full bg-slate-800 px-3 py-1 text-red-200">
                  Score {Number(alert.anomaly_score).toFixed(2)}
                </span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-200">
                  CPU {Number(alert.metrics?.cpu_usage ?? 0).toFixed(1)}%
                </span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-200">
                  Memory {Number(alert.metrics?.memory_usage ?? 0).toFixed(1)}%
                </span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-200">
                  Response {Number(alert.metrics?.response_time ?? 0).toFixed(1)} ms
                </span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-200">
                  Error {Number(alert.metrics?.error_rate ?? 0).toFixed(2)}%
                </span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-200">
                  Restarts {Number(alert.metrics?.pod_restarts ?? 0)}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {(alert.recommended_actions ?? []).map((action) => (
                  <span
                    key={action}
                    className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs text-amber-100"
                  >
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {action}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
