import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { format } from "date-fns";
import { Activity, Clock3 } from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/alerts", label: "Alerts" },
  { to: "/model", label: "Model Info" },
];

function navClassName({ isActive }) {
  return [
    "rounded-full px-4 py-2 text-sm font-medium transition-all duration-300",
    isActive
      ? "bg-cyan-500/15 text-cyan-300 shadow-cyanGlow"
      : "text-slate-300 hover:bg-slate-800/80 hover:text-white",
  ].join(" ");
}

export default function Header({ isConnected }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <span
            className={[
              "h-3 w-3 rounded-full animate-pulse-dot",
              isConnected ? "bg-emerald-400" : "bg-red-400 glow-red",
            ].join(" ")}
          />
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-lg font-bold tracking-wide text-cyan-400">
              <Activity className="h-5 w-5" />
              <span>K8s AIOps</span>
            </div>
            <p className="truncate text-xs text-slate-400">Real-time anomaly detection dashboard</p>
          </div>
        </div>

        <nav className="hidden items-center gap-2 md:flex">
          {navItems.map((item) => (
            <NavLink key={item.to} className={navClassName} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div
            className={[
              "hidden items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold sm:flex",
              isConnected
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border-red-500/30 bg-red-500/10 text-red-300",
            ].join(" ")}
          >
            <span
              className={[
                "h-2.5 w-2.5 rounded-full",
                isConnected ? "bg-emerald-400 animate-pulse-dot" : "bg-red-400",
              ].join(" ")}
            />
            {isConnected ? "LIVE" : "OFFLINE"}
          </div>

          <div className="rounded-full border border-slate-700/70 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <Clock3 className="h-3.5 w-3.5 text-cyan-300" />
              <span>{format(currentTime, "HH:mm:ss")}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-slate-800/60 px-4 py-2 md:hidden">
        <div className="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto">
          {navItems.map((item) => (
            <NavLink key={item.to} className={navClassName} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </header>
  );
}
