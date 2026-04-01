import { useEffect, useMemo, useRef, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AlertTriangle, WifiOff } from "lucide-react";
import Header from "./components/Header";
import SessionStats from "./components/SessionStats";
import PodTable from "./components/PodTable";
import AnomalyChart from "./components/AnomalyChart";
import AlertFeed from "./components/AlertFeed";
import ModelInfoCard from "./components/ModelInfoCard";
import HistoricalAlerts from "./components/HistoricalAlerts";

const emptyStats = {
  total_pods: 0,
  anomalies_this_iteration: 0,
  total_anomalies: 0,
  anomaly_rate: 0,
  uptime_seconds: 0,
};

function DashboardPage({ pods, scoreHistory, sessionAlerts, stats, iteration, isConnected }) {
  return (
    <div className="space-y-6">
      <SessionStats stats={stats} iteration={iteration} />
      <div className="grid gap-6 xl:grid-cols-2">
        <AnomalyChart scoreHistory={scoreHistory} />
        <AlertFeed alerts={sessionAlerts} isConnected={isConnected} />
      </div>
      <PodTable pods={pods} isConnected={isConnected} />
    </div>
  );
}

export default function App() {
  const [pods, setPods] = useState([]);
  const [sessionAlerts, setSessionAlerts] = useState([]);
  const [scoreHistory, setScoreHistory] = useState([]);
  const [stats, setStats] = useState(emptyStats);
  const [iteration, setIteration] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [hasLivePayload, setHasLivePayload] = useState(false);

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    const connect = () => {
      if (!isMounted) {
        return;
      }

      const socket = new WebSocket("ws://localhost:8000/ws/monitor");
      socketRef.current = socket;

      socket.onopen = () => {
        if (!isMounted) {
          return;
        }
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        if (!isMounted) {
          return;
        }

        try {
          const payload = JSON.parse(event.data);
          setIteration(payload.iteration ?? 0);
          setPods(payload.pods ?? []);
          setSessionAlerts(payload.session_alerts ?? []);
          setScoreHistory(payload.score_history ?? []);
          setStats(payload.stats ?? emptyStats);
          setHasLivePayload(true);
        } catch (error) {
          console.error("Failed to parse WebSocket payload", error);
        }
      };

      socket.onclose = () => {
        if (!isMounted) {
          return;
        }

        setIsConnected(false);
        socketRef.current = null;
        reconnectTimerRef.current = window.setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket.close();
      };
    };

    connect();

    return () => {
      isMounted = false;
      window.clearTimeout(reconnectTimerRef.current);
      socketRef.current?.close();
    };
  }, []);

  const banner = useMemo(() => {
    if (isConnected) {
      return null;
    }

    return hasLivePayload
      ? {
          icon: AlertTriangle,
          title: "Live connection interrupted",
          description: "Showing the most recent dashboard data while the app retries the WebSocket connection.",
        }
      : {
          icon: WifiOff,
          title: "Backend Offline",
          description: "Start the FastAPI backend on port 8000 to enable live metrics, alerts, and model endpoints.",
        };
  }, [hasLivePayload, isConnected]);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-dashboard text-slate-100">
        <Header isConnected={isConnected} />
        <main className="mx-auto max-w-7xl px-4 pb-10 pt-24 sm:px-6 lg:px-8">
          {banner ? (
            <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-100 shadow-amberGlow transition-all duration-300">
              <banner.icon className="mt-0.5 h-5 w-5 flex-shrink-0" />
              <div>
                <p className="font-semibold">{banner.title}</p>
                <p className="text-sm text-amber-50/80">{banner.description}</p>
              </div>
            </div>
          ) : null}

          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  pods={pods}
                  scoreHistory={scoreHistory}
                  sessionAlerts={sessionAlerts}
                  stats={stats}
                  iteration={iteration}
                  isConnected={isConnected}
                />
              }
            />
            <Route path="/alerts" element={<HistoricalAlerts />} />
            <Route path="/model" element={<ModelInfoCard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
