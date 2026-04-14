"use client";

import { useEffect, useState } from "react";

interface ModelRun {
  run_id: string;
  model_name: string;
  params: Record<string, string>;
  metrics: Record<string, number>;
}

function fmt(v: number | undefined, decimals = 5) {
  if (v === undefined || v === null) return "—";
  return v.toFixed(decimals);
}

function pct(v: number | undefined) {
  if (v === undefined || v === null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

export default function ModelLeaderboard() {
  const [runs, setRuns] = useState<ModelRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/inference/models")
      .then((r) => r.json())
      .then((data) => {
        setRuns(data.runs ?? []);
        setLoading(false);
      })
      .catch(() => {
        setError("Inference service unavailable");
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">Model Leaderboard</h2>

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="pb-2 pr-4">Model</th>
                <th className="pb-2 pr-4">Val MAE</th>
                <th className="pb-2 pr-4">Test MAE</th>
                <th className="pb-2 pr-4">Val Dir%</th>
                <th className="pb-2">Test Dir%</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.run_id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="py-2 pr-4 font-medium text-slate-200">{run.model_name}</td>
                  <td className="py-2 pr-4 text-slate-300">{fmt(run.metrics["val_mae"])}</td>
                  <td className="py-2 pr-4 text-slate-300">{fmt(run.metrics["test_mae"])}</td>
                  <td className="py-2 pr-4 text-slate-300">{pct(run.metrics["val_dir_accuracy"])}</td>
                  <td className="py-2 text-slate-300">{pct(run.metrics["test_dir_accuracy"])}</td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-slate-400 text-center">No runs found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
