import { useState } from "react";
import Overview from "./pages/Overview";
import EtsCore from "./pages/EtsCore";
import ShippingMrv from "./pages/ShippingMrv";
import Cbam from "./pages/Cbam";
import Credits from "./pages/Credits";
import Verification from "./pages/Verification";
import Trading from "./pages/Trading";

const TABS = [
  { key: "overview", label: "Overview", component: Overview },
  { key: "ets", label: "EU ETS core", component: EtsCore },
  { key: "shipping", label: "Shipping MRV", component: ShippingMrv },
  { key: "cbam", label: "CBAM", component: Cbam },
  { key: "credits", label: "Credit sourcing", component: Credits },
  { key: "verification", label: "Verification", component: Verification },
  { key: "trading", label: "Trading", component: Trading },
];

export default function App() {
  const [active, setActive] = useState("overview");
  const ActiveComponent = TABS.find((t) => t.key === active)?.component ?? Overview;

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Carbon Compliance &amp; Trading Platform</h1>
            <p className="text-xs text-slate-400">EU ETS · Shipping MRV · CBAM · Credit sourcing · Verification · Trading</p>
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-6 flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setActive(t.key)}
              className={`px-3 py-2 text-sm font-medium border-b-2 whitespace-nowrap transition ${
                active === t.key
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-6">
        <ActiveComponent />
      </main>
    </div>
  );
}
