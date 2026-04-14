"use client";

import { useEffect, useState } from "react";

interface FeatureStatus {
  psi: number;
  status: "OK" | "WARNING" | "ALERT";
}

interface DriftResponse {
  features: Record<string, FeatureStatus>;
}

const STATUS_COLORS: Record<string, string> = {
  OK: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  WARNING: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  ALERT: "bg-red-500/20 text-red-400 border border-red-500/30",
};

const PSI_BAR_COLORS: Record<string, string> = {
  OK: "bg-emerald-500",
  WARNING: "bg-yellow-500",
  ALERT: "bg-red-500",
};

export default function DriftPanel() {
  const [features, setFeatures] = useState<Record<string, FeatureStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  async function fetchDrift() {
    try {
      const r = await fetch("/api/drift/status");
      const data: DriftResponse = await r.json();
      setFeatures(data.features);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch {
      setError("Drift service unavailable");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDrift();
  }, []);

  const alertCount = Object.values(features).filter((f) => f.status === "ALERT").length;
  const warnCount = Object.values(features).filter((f) => f.status === "WARNING").length;

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Feature Drift (PSI)</h2>
        <div className="flex items-center gap-3">
          {!loading && !error && (
            <div className="flex gap-2 text-xs">
              {alertCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30">
                  {alertCount} alert{alertCount > 1 ? "s" : ""}
                </span>
              )}
              {warnCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                  {warnCount} warning{warnCount > 1 ? "s" : ""}
                </span>
              )}
            </div>
          )}
          <button
            onClick={fetchDrift}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && (
        <>
          <div className="space-y-3">
            {Object.entries(features).map(([name, { psi, status }]) => (
              <div key={name} className="flex items-center gap-4">
                <span className="w-36 text-sm text-slate-300 font-mono">{name}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${PSI_BAR_COLORS[status]}`}
                    style={{ width: `${Math.min(psi / 0.4, 1) * 100}%` }}
                  />
                </div>
                <span className="w-16 text-xs text-slate-400 text-right font-mono">{psi.toFixed(4)}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full w-16 text-center ${STATUS_COLORS[status]}`}>
                  {status}
                </span>
              </div>
            ))}
            {Object.keys(features).length === 0 && (
              <p className="text-slate-400 text-sm">No drift data available — is the drift service running?</p>
            )}
          </div>
          {lastUpdated && (
            <p className="text-xs text-slate-500 mt-4">Last updated: {lastUpdated}</p>
          )}
        </>
      )}

      <div className="flex gap-4 mt-4 text-xs text-slate-500">
        <span>PSI &lt;0.1 = OK</span>
        <span>0.1–0.2 = WARNING</span>
        <span>&gt;0.2 = ALERT</span>
      </div>
    </div>
  );
}
