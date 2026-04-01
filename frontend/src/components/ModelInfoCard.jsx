import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import { AlertTriangle, BarChart3, Brain, Database, Loader2 } from "lucide-react";

function RingMetric({ label, value, color }) {
  const safeValue = Number(value ?? 0);
  const percentage = Math.max(0, Math.min(1, safeValue));
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - percentage * circumference;

  return (
    <div className="glass-card flex flex-col items-center justify-center p-6 text-center">
      <div className="relative mb-4 h-32 w-32">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" fill="none" r={radius} stroke="rgba(51, 65, 85, 0.9)" strokeWidth="10" />
          <circle
            cx="60"
            cy="60"
            fill="none"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            strokeWidth="10"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-white">{safeValue.toFixed(3)}</span>
        </div>
      </div>
      <p className="text-sm uppercase tracking-wider text-slate-400">{label}</p>
    </div>
  );
}

function formatTrainingDate(value) {
  if (!value) {
    return "Unavailable";
  }

  try {
    return format(new Date(value), "PPP p");
  } catch (_error) {
    return value;
  }
}

export default function ModelInfoCard() {
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function fetchModelInfo() {
      try {
        const response = await fetch("/api/model");
        if (!response.ok) {
          throw new Error("Failed to load model metadata");
        }
        const payload = await response.json();
        if (isMounted) {
          setModelInfo(payload);
          setError("");
        }
      } catch (_fetchError) {
        if (isMounted) {
          setError("Model metadata is unavailable. Start the backend to inspect the trained model.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchModelInfo();
    return () => {
      isMounted = false;
    };
  }, []);

  const features = useMemo(() => modelInfo?.features ?? [], [modelInfo]);

  if (loading) {
    return (
      <section className="glass-card flex min-h-96 items-center justify-center p-8">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-cyan-400" />
          <p className="mt-4 text-slate-300">Loading model metadata...</p>
        </div>
      </section>
    );
  }

  if (error || !modelInfo) {
    return (
      <section className="glass-card flex min-h-96 items-center justify-center p-8">
        <div className="max-w-lg text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-amber-400" />
          <h1 className="mt-4 text-2xl font-semibold text-white">Model Info Unavailable</h1>
          <p className="mt-3 text-slate-400">{error}</p>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="glass-card overflow-hidden p-0">
        <div className="bg-gradient-to-r from-cyan-500/10 via-slate-900/60 to-emerald-500/10 px-6 py-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-cyan-200">
                <Brain className="h-4 w-4" />
                Production Model
              </div>
              <h1 className="text-3xl font-bold text-white">Random Forest Classifier</h1>
              <p className="mt-2 text-slate-300">Training date: {formatTrainingDate(modelInfo.training_date)}</p>
            </div>
            <div className="rounded-2xl border border-slate-700/70 bg-slate-950/70 px-5 py-4">
              <p className="text-sm uppercase tracking-wider text-slate-400">Threshold</p>
              <p className="mt-2 text-3xl font-bold text-cyan-300">{Number(modelInfo.threshold ?? 0).toFixed(2)}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <RingMetric color="#10b981" label="F1-Score" value={modelInfo.f1} />
        <RingMetric color="#06b6d4" label="AUC" value={modelInfo.auc} />
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <article className="glass-card p-6 xl:col-span-2">
          <div className="mb-5 flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-cyan-300" />
            <h2 className="text-xl font-semibold text-white">Selected Features</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {features.map((feature) => (
              <span
                key={feature}
                className="rounded-full border border-slate-700/70 bg-slate-900/80 px-4 py-2 text-sm text-slate-200"
              >
                {feature}
              </span>
            ))}
          </div>
        </article>

        <article className="glass-card p-6">
          <div className="mb-5 flex items-center gap-3">
            <Database className="h-5 w-5 text-cyan-300" />
            <h2 className="text-xl font-semibold text-white">Model Metadata</h2>
          </div>
          <dl className="space-y-4 text-sm">
            <div className="rounded-xl bg-slate-900/70 p-4">
              <dt className="text-slate-400">Model Type</dt>
              <dd className="mt-1 text-base font-semibold capitalize text-white">{modelInfo.model_type ?? "Unknown"}</dd>
            </div>
            <div className="rounded-xl bg-slate-900/70 p-4">
              <dt className="text-slate-400">Threshold</dt>
              <dd className="mt-1 text-base font-semibold text-white">{Number(modelInfo.threshold ?? 0).toFixed(2)}</dd>
            </div>
            <div className="rounded-xl bg-slate-900/70 p-4">
              <dt className="text-slate-400">Total Features</dt>
              <dd className="mt-1 text-base font-semibold text-white">{modelInfo.total_features ?? 0}</dd>
            </div>
            <div className="rounded-xl bg-slate-900/70 p-4">
              <dt className="text-slate-400">Training Date</dt>
              <dd className="mt-1 text-base font-semibold text-white">{formatTrainingDate(modelInfo.training_date)}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="glass-card p-6">
        <h2 className="text-xl font-semibold text-white">Anomaly Threshold Scale</h2>
        <p className="mt-2 text-sm text-slate-400">
          Scores below 0.60 are treated as normal, 0.60 and above enter the alert region, and 0.80+ is considered high severity.
        </p>
        <div className="mt-6 rounded-2xl border border-slate-700/70 bg-slate-900/70 p-5">
          <div className="relative h-5 overflow-hidden rounded-full bg-slate-800">
            <div className="absolute inset-y-0 left-0 w-3/5 bg-emerald-500/80" />
            <div className="absolute inset-y-0 left-3/5 w-1/5 bg-amber-500/80" />
            <div className="absolute inset-y-0 right-0 w-1/5 bg-red-500/80" />
            <div
              className="absolute -bottom-1.5 -top-1.5 w-1 rounded-full bg-white"
              style={{ left: `${Math.min(Math.max(Number(modelInfo.threshold ?? 0) * 100, 0), 100)}%` }}
            />
          </div>
          <div className="mt-3 grid gap-2 text-sm text-slate-300 sm:grid-cols-3">
            <div>Normal: 0.00 - 0.59</div>
            <div>Medium Alert Zone: 0.60 - 0.79</div>
            <div>High Severity: 0.80 - 1.00</div>
          </div>
        </div>
      </section>
    </div>
  );
}
