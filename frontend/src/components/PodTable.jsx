import { useMemo } from "react";
import { format } from "date-fns";
import { Info, Loader2 } from "lucide-react";

function severityClasses(severity) {
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

function statusClasses(isAnomaly) {
  return isAnomaly
    ? "border-red-500/30 bg-red-500/10 text-red-200"
    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
}

function scoreBarClasses(score) {
  if (score > 0.8) {
    return "bg-red-400";
  }
  if (score >= 0.5) {
    return "bg-amber-400";
  }
  return "bg-emerald-400";
}

function formatTime(value) {
  if (!value) {
    return "--";
  }

  try {
    return format(new Date(value), "PPP p");
  } catch (_error) {
    return value;
  }
}

export default function PodTable({ pods, isConnected }) {
  const lastUpdated = useMemo(() => {
    if (!pods.length) {
      return null;
    }

    const timestamps = pods
      .map((pod) => pod.timestamp)
      .filter(Boolean)
      .sort((left, right) => new Date(right).getTime() - new Date(left).getTime());

    return timestamps[0] ?? null;
  }, [pods]);

  return (
    <section className="glass-card p-5 shadow-lg shadow-slate-950/30">
      <div className="mb-5 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Live Pod Status</h2>
          <p className="text-sm text-slate-400">Updates every 10s</p>
        </div>
        <div className="text-sm text-slate-400">
          {isConnected ? "Streaming from backend monitor" : "Awaiting live connection"}
        </div>
      </div>

      {!pods.length ? (
        <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/70 bg-slate-900/40 text-center">
          <Loader2 className="mb-4 h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-lg font-medium text-white">Waiting for pod data...</p>
          <p className="mt-2 text-sm text-slate-400">Live pod metrics will appear here as soon as the backend publishes a snapshot.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-slate-400">
                <th className="pb-4 pr-4">Pod Name</th>
                <th className="pb-4 pr-4">Status</th>
                <th className="pb-4 pr-4">Anomaly Score</th>
                <th className="pb-4 pr-4">CPU%</th>
                <th className="pb-4 pr-4">Memory%</th>
                <th className="pb-4 pr-4">Restarts</th>
                <th className="pb-4 pr-4">Severity</th>
                <th className="pb-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {pods.map((pod) => (
                <tr
                  key={`${pod.pod_name}-${pod.timestamp}`}
                  className={[
                    "transition-all duration-300",
                    pod.is_anomaly ? "border-l-2 border-red-500 bg-red-500/5" : "",
                  ].join(" ")}
                >
                  <td className="py-4 pr-4">
                    <div className="font-medium text-white">{pod.pod_name}</div>
                    <div className="text-sm text-slate-400">{pod.namespace}</div>
                  </td>
                  <td className="py-4 pr-4">
                    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusClasses(pod.is_anomaly)}`}>
                      {pod.is_anomaly ? "ANOMALY" : "NORMAL"}
                    </span>
                  </td>
                  <td className="py-4 pr-4">
                    <div className="flex min-w-44 items-center gap-3">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${scoreBarClasses(pod.anomaly_score)}`}
                          style={{ width: `${Math.min(pod.anomaly_score * 100, 100)}%` }}
                        />
                      </div>
                      <span className="w-12 text-right text-sm font-medium tabular-nums text-slate-200">
                        {pod.anomaly_score.toFixed(2)}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 pr-4">
                    <div className="min-w-24">
                      <div className="mb-1 text-sm tabular-nums text-slate-200">{pod.cpu_usage.toFixed(1)}%</div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-cyan-400 transition-all duration-300"
                          style={{ width: `${Math.min(pod.cpu_usage, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-4 pr-4">
                    <div className="min-w-24">
                      <div className="mb-1 text-sm tabular-nums text-slate-200">{pod.memory_usage.toFixed(1)}%</div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-violet-400 transition-all duration-300"
                          style={{ width: `${Math.min(pod.memory_usage, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-4 pr-4 text-sm tabular-nums text-slate-200">{pod.pod_restarts}</td>
                  <td className="py-4 pr-4">
                    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold capitalize ${severityClasses(pod.severity)}`}>
                      {pod.severity}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className="group relative inline-flex">
                      <button
                        className="rounded-lg border border-slate-700 bg-slate-900/80 p-2 text-slate-300 transition-all duration-300 hover:border-cyan-400 hover:text-cyan-300"
                        type="button"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                      <div className="pointer-events-none absolute right-0 top-12 z-20 hidden w-72 rounded-xl border border-slate-700/70 bg-slate-950/95 p-3 text-sm text-slate-200 shadow-xl shadow-slate-950/50 group-hover:block">
                        {pod.recommended_actions?.length ? (
                          <ul className="space-y-2">
                            {pod.recommended_actions.map((action) => (
                              <li key={action} className="rounded-lg bg-slate-900/80 px-3 py-2">
                                {action}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p>No recommended actions for this pod right now.</p>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 border-t border-slate-800 pt-4 text-sm text-slate-400">
        Last update: <span className="text-slate-200">{formatTime(lastUpdated)}</span>
      </div>
    </section>
  );
}
