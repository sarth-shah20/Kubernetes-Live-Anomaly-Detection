import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  AlertTriangle,
  ArrowDownUp,
  ChevronLeft,
  ChevronRight,
  Database,
  Download,
  Filter,
  Loader2,
  Search,
} from "lucide-react";

const pageSize = 20;

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

function rowTint(severity) {
  switch (severity) {
    case "high":
      return "bg-red-500/5";
    case "medium":
      return "bg-amber-500/5";
    case "low":
      return "bg-yellow-500/5";
    default:
      return "";
  }
}

function formatDateTime(value) {
  try {
    return format(new Date(value), "PPP p");
  } catch (_error) {
    return value;
  }
}

function getDateOnly(value) {
  try {
    return format(new Date(value), "yyyy-MM-dd");
  } catch (_error) {
    return "";
  }
}

function getSortableValue(alert, key) {
  switch (key) {
    case "timestamp":
      return new Date(alert.timestamp).getTime();
    case "pod_name":
      return alert.pod_name ?? "";
    case "severity":
      return alert.severity ?? "";
    case "anomaly_score":
      return Number(alert.anomaly_score ?? 0);
    case "cpu_usage":
      return Number(alert.metrics?.cpu_usage ?? 0);
    case "memory_usage":
      return Number(alert.metrics?.memory_usage ?? 0);
    case "response_time":
      return Number(alert.metrics?.response_time ?? 0);
    case "actions":
      return (alert.recommended_actions ?? []).join(" | ");
    default:
      return "";
  }
}

export default function HistoricalAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [severity, setSeverity] = useState("all");
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: "timestamp", direction: "desc" });
  const [page, setPage] = useState(1);

  useEffect(() => {
    let isMounted = true;

    async function fetchHistoricalAlerts() {
      try {
        const response = await fetch("/api/alerts/historical");
        if (!response.ok) {
          throw new Error("Failed to load historical alerts");
        }
        const payload = await response.json();
        if (isMounted) {
          setAlerts(Array.isArray(payload) ? payload : []);
        }
      } catch (_fetchError) {
        if (isMounted) {
          setError("Historical alert data is unavailable. Start the backend to inspect saved alert history.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchHistoricalAlerts();
    return () => {
      isMounted = false;
    };
  }, []);

  const uniqueDates = useMemo(() => {
    return Array.from(new Set(alerts.map((alert) => getDateOnly(alert.timestamp)).filter(Boolean))).sort();
  }, [alerts]);

  const filteredAlerts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return alerts.filter((alert) => {
      if (severity !== "all" && alert.severity !== severity) {
        return false;
      }

      if (query && !String(alert.pod_name ?? "").toLowerCase().includes(query)) {
        return false;
      }

      const alertDate = getDateOnly(alert.timestamp);
      if (startDate && alertDate < startDate) {
        return false;
      }
      if (endDate && alertDate > endDate) {
        return false;
      }

      return true;
    });
  }, [alerts, endDate, search, severity, startDate]);

  const sortedAlerts = useMemo(() => {
    const next = [...filteredAlerts];
    next.sort((left, right) => {
      const leftValue = getSortableValue(left, sortConfig.key);
      const rightValue = getSortableValue(right, sortConfig.key);

      if (leftValue < rightValue) {
        return sortConfig.direction === "asc" ? -1 : 1;
      }
      if (leftValue > rightValue) {
        return sortConfig.direction === "asc" ? 1 : -1;
      }
      return 0;
    });
    return next;
  }, [filteredAlerts, sortConfig]);

  const totalPages = Math.max(1, Math.ceil(sortedAlerts.length / pageSize));
  const paginatedAlerts = useMemo(() => {
    const startIndex = (page - 1) * pageSize;
    return sortedAlerts.slice(startIndex, startIndex + pageSize);
  }, [page, sortedAlerts]);

  useEffect(() => {
    setPage(1);
  }, [severity, search, startDate, endDate, sortConfig]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const summary = useMemo(() => {
    const uniquePods = new Set(filteredAlerts.map((alert) => alert.pod_name));
    return {
      total: filteredAlerts.length,
      high: filteredAlerts.filter((alert) => alert.severity === "high").length,
      medium: filteredAlerts.filter((alert) => alert.severity === "medium").length,
      uniquePods: uniquePods.size,
    };
  }, [filteredAlerts]);

  const handleSort = (key) => {
    setSortConfig((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  };

  const exportCsv = () => {
    if (!sortedAlerts.length) {
      return;
    }

    const headers = [
      "timestamp",
      "pod_name",
      "severity",
      "anomaly_score",
      "cpu_usage",
      "memory_usage",
      "response_time",
      "error_rate",
      "pod_restarts",
      "recommended_actions",
    ];

    const rows = sortedAlerts.map((alert) => [
      alert.timestamp,
      alert.pod_name,
      alert.severity,
      alert.anomaly_score,
      alert.metrics?.cpu_usage ?? "",
      alert.metrics?.memory_usage ?? "",
      alert.metrics?.response_time ?? "",
      alert.metrics?.error_rate ?? "",
      alert.metrics?.pod_restarts ?? "",
      (alert.recommended_actions ?? []).join(" | "),
    ]);

    const csv = [headers, ...rows]
      .map((row) =>
        row
          .map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`)
          .join(","),
      )
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "historical-alerts.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const columns = [
    { key: "timestamp", label: "Timestamp" },
    { key: "pod_name", label: "Pod Name" },
    { key: "severity", label: "Severity" },
    { key: "anomaly_score", label: "Anomaly Score" },
    { key: "cpu_usage", label: "CPU%" },
    { key: "memory_usage", label: "Memory%" },
    { key: "response_time", label: "Response Time" },
    { key: "actions", label: "Actions" },
  ];

  if (loading) {
    return (
      <section className="glass-card flex min-h-96 items-center justify-center p-8">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-cyan-400" />
          <p className="mt-4 text-slate-300">Loading historical alerts...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="glass-card flex min-h-96 items-center justify-center p-8">
        <div className="max-w-lg text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-amber-400" />
          <h1 className="mt-4 text-2xl font-semibold text-white">Historical Alerts Unavailable</h1>
          <p className="mt-3 text-slate-400">{error}</p>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="glass-card p-5">
          <p className="text-sm text-slate-400">Total Alerts</p>
          <p className="mt-2 text-3xl font-bold text-white">{summary.total}</p>
        </article>
        <article className="glass-card p-5">
          <p className="text-sm text-slate-400">High Severity</p>
          <p className="mt-2 text-3xl font-bold text-red-300">{summary.high}</p>
        </article>
        <article className="glass-card p-5">
          <p className="text-sm text-slate-400">Medium Severity</p>
          <p className="mt-2 text-3xl font-bold text-amber-300">{summary.medium}</p>
        </article>
        <article className="glass-card p-5">
          <p className="text-sm text-slate-400">Unique Pods Affected</p>
          <p className="mt-2 text-3xl font-bold text-cyan-300">{summary.uniquePods}</p>
        </article>
      </section>

      <section className="glass-card p-5">
        <div className="mb-5 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white">Historical Alerts</h1>
            <p className="mt-1 text-sm text-slate-400">Filter, sort, paginate, and export the saved anomaly history.</p>
          </div>
          <button
            className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-200 transition-all duration-300 hover:bg-cyan-500/15"
            onClick={exportCsv}
            type="button"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>

        <div className="mb-5 grid gap-4 lg:grid-cols-3 xl:grid-cols-5">
          <label className="glass-card flex items-center gap-3 px-4 py-3">
            <Filter className="h-4 w-4 text-cyan-300" />
            <select
              className="w-full bg-transparent text-sm text-slate-100 outline-none"
              onChange={(event) => setSeverity(event.target.value)}
              value={severity}
            >
              <option className="bg-slate-950" value="all">
                All severities
              </option>
              <option className="bg-slate-950" value="high">
                High
              </option>
              <option className="bg-slate-950" value="medium">
                Medium
              </option>
              <option className="bg-slate-950" value="low">
                Low
              </option>
            </select>
          </label>

          <label className="glass-card flex items-center gap-3 px-4 py-3 lg:col-span-2">
            <Search className="h-4 w-4 text-cyan-300" />
            <input
              className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search pod name"
              value={search}
            />
          </label>

          {uniqueDates.length > 1 ? (
            <>
              <label className="glass-card px-4 py-3">
                <span className="mb-2 block text-xs uppercase tracking-wider text-slate-500">Start date</span>
                <input
                  className="w-full bg-transparent text-sm text-slate-100 outline-none"
                  max={endDate || undefined}
                  onChange={(event) => setStartDate(event.target.value)}
                  type="date"
                  value={startDate}
                />
              </label>
              <label className="glass-card px-4 py-3">
                <span className="mb-2 block text-xs uppercase tracking-wider text-slate-500">End date</span>
                <input
                  className="w-full bg-transparent text-sm text-slate-100 outline-none"
                  min={startDate || undefined}
                  onChange={(event) => setEndDate(event.target.value)}
                  type="date"
                  value={endDate}
                />
              </label>
            </>
          ) : null}
        </div>

        {!sortedAlerts.length ? (
          <div className="flex min-h-80 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/70 bg-slate-900/50 text-center">
            <Database className="mb-4 h-10 w-10 text-cyan-400" />
            <p className="text-lg font-medium text-white">No matching historical alerts</p>
            <p className="mt-2 text-sm text-slate-400">Adjust your filters or start a monitoring session to populate saved alert history.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-slate-400">
                    {columns.map((column) => (
                      <th key={column.key} className="pb-4 pr-4">
                        <button
                          className="inline-flex items-center gap-2 text-left transition-all duration-300 hover:text-cyan-300"
                          onClick={() => handleSort(column.key)}
                          type="button"
                        >
                          {column.label}
                          <ArrowDownUp className="h-3.5 w-3.5" />
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {paginatedAlerts.map((alert) => (
                    <tr key={`${alert.pod_name}-${alert.timestamp}`} className={`transition-all duration-300 ${rowTint(alert.severity)}`}>
                      <td className="py-4 pr-4 text-sm text-slate-200">{formatDateTime(alert.timestamp)}</td>
                      <td className="py-4 pr-4">
                        <div className="font-medium text-white">{alert.pod_name}</div>
                        <div className="text-xs text-slate-400">{alert.namespace}</div>
                      </td>
                      <td className="py-4 pr-4">
                        <span className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${severityBadge(alert.severity)}`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="py-4 pr-4 text-sm font-medium text-slate-100">{Number(alert.anomaly_score ?? 0).toFixed(2)}</td>
                      <td className="py-4 pr-4 text-sm text-slate-200">{Number(alert.metrics?.cpu_usage ?? 0).toFixed(1)}%</td>
                      <td className="py-4 pr-4 text-sm text-slate-200">{Number(alert.metrics?.memory_usage ?? 0).toFixed(1)}%</td>
                      <td className="py-4 pr-4 text-sm text-slate-200">{Number(alert.metrics?.response_time ?? 0).toFixed(1)} ms</td>
                      <td className="py-4 text-sm text-slate-300">
                        {(alert.recommended_actions ?? []).join(" | ") || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-5 flex flex-col gap-4 border-t border-slate-800 pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-400">
                Page <span className="text-slate-200">{page}</span> of <span className="text-slate-200">{totalPages}</span>
              </p>
              <div className="flex items-center gap-3">
                <button
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-700/70 bg-slate-900/80 px-3 py-2 text-sm text-slate-200 transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={page === 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  type="button"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Prev
                </button>
                <button
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-700/70 bg-slate-900/80 px-3 py-2 text-sm text-slate-200 transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={page === totalPages}
                  onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                  type="button"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
