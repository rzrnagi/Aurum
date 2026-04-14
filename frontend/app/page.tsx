import ForecastChart from "./components/ForecastChart";
import ModelLeaderboard from "./components/ModelLeaderboard";
import DriftPanel from "./components/DriftPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="border-b border-slate-700 pb-4">
          <h1 className="text-2xl font-bold text-slate-100">FinSignal</h1>
          <p className="text-sm text-slate-400 mt-1">S&P 500 return forecasting &amp; feature drift monitoring</p>
        </div>

        <ForecastChart />
        <ModelLeaderboard />
        <DriftPanel />
      </div>
    </main>
  );
}
