"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

interface PredictResponse {
  ticker: string;
  forecast_date: string;
  horizon_days: number;
  predicted_return: number;
  ci_lower: number;
  ci_upper: number;
  model: string;
}

const HORIZONS = [1, 5, 21];

export default function ForecastChart() {
  const [data, setData] = useState<{ horizon: number; predicted: number; lower: number; upper: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<{ ticker: string; date: string; model: string } | null>(null);

  useEffect(() => {
    async function fetch_predictions() {
      try {
        const results = await Promise.all(
          HORIZONS.map((h) =>
            fetch(`/api/inference/predict?ticker=GSPC&horizon=${h}`)
              .then((r) => r.json() as Promise<PredictResponse>)
          )
        );
        setData(
          results.map((r) => ({
            horizon: r.horizon_days,
            predicted: parseFloat((r.predicted_return * 100).toFixed(4)),
            lower: parseFloat((r.ci_lower * 100).toFixed(4)),
            upper: parseFloat((r.ci_upper * 100).toFixed(4)),
          }))
        );
        setMeta({ ticker: results[0].ticker, date: results[0].forecast_date, model: results[0].model });
      } catch {
        setError("Inference service unavailable");
      } finally {
        setLoading(false);
      }
    }
    fetch_predictions();
  }, []);

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">S&P 500 Forecast</h2>
        {meta && (
          <span className="text-xs text-slate-400">
            {meta.ticker} · {meta.date} · {meta.model}
          </span>
        )}
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading...</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="horizon"
              tickFormatter={(v) => `${v}d`}
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              label={{ value: "Horizon (days)", position: "insideBottom", offset: -2, fill: "#94a3b8", fontSize: 12 }}
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "none", borderRadius: 8 }}
              formatter={(v) => [`${v}%`]}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="upper" stroke="#38bdf8" strokeDasharray="4 4" dot={false} name="CI Upper" />
            <Line type="monotone" dataKey="predicted" stroke="#818cf8" strokeWidth={2} dot={{ r: 4 }} name="Predicted Return %" />
            <Line type="monotone" dataKey="lower" stroke="#38bdf8" strokeDasharray="4 4" dot={false} name="CI Lower" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
