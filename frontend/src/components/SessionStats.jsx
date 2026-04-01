import { AlertTriangle, Clock3, RefreshCw, Server, TrendingUp } from "lucide-react";

function formatUptime(value) {
  const totalSeconds = Math.max(0, Math.floor(value ?? 0));
  const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function anomalyRateCardClasses(rate) {
  if (rate > 50) {
    return "border-red-500/30 bg-red-500/10 text-red-100 glow-red";
  }
  if (rate >= 20) {
    return "border-amber-500/30 bg-amber-500/10 text-amber-100 glow-amber";
  }
  return "border-emerald-500/30 bg-emerald-500/10 text-emerald-100";
}

export default function SessionStats({ stats, iteration }) {
  const cards = [
    {
      label: "Total Pods",
      value: stats.total_pods ?? 0,
      icon: Server,
      color: "text-cyan-300",
      extraClass: "",
    },
    {
      label: "Anomalies Detected",
      value: stats.total_anomalies ?? 0,
      icon: AlertTriangle,
      color: "text-red-300",
      extraClass: "",
    },
    {
      label: "Anomaly Rate %",
      value: `${(stats.anomaly_rate ?? 0).toFixed(1)}%`,
      icon: TrendingUp,
      color: "text-amber-200",
      extraClass: anomalyRateCardClasses(stats.anomaly_rate ?? 0),
    },
    {
      label: "Monitoring Iterations",
      value: iteration ?? 0,
      icon: RefreshCw,
      color: "text-violet-300",
      extraClass: "",
    },
    {
      label: "Uptime",
      value: formatUptime(stats.uptime_seconds ?? 0),
      icon: Clock3,
      color: "text-emerald-300",
      extraClass: "",
    },
  ];

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <article
            key={card.label}
            className={[
              "glass-card p-5 shadow-lg shadow-slate-950/30",
              card.extraClass,
            ].join(" ")}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-slate-400">{card.label}</p>
                <p className="mt-3 text-3xl font-bold tracking-tight text-white transition-all duration-300">
                  <span className="tabular-nums">{card.value}</span>
                </p>
              </div>
              <div className="rounded-xl border border-slate-700/70 bg-slate-900/80 p-3">
                <Icon className={`h-5 w-5 ${card.color}`} />
              </div>
            </div>
          </article>
        );
      })}
    </section>
  );
}
