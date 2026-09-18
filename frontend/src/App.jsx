import { useState } from "react";
import { useAuth } from "./auth";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import EtsCore from "./pages/EtsCore";
import ShippingMrv from "./pages/ShippingMrv";
import Cbam from "./pages/Cbam";
import Credits from "./pages/Credits";
import Verification from "./pages/Verification";
import Trading from "./pages/Trading";
import IndiaCcts from "./pages/IndiaCcts";

const TABS = [
  { key: "overview", label: "Overview", component: Overview },
  { key: "ets", label: "EU ETS core", component: EtsCore },
  { key: "shipping", label: "Shipping MRV", component: ShippingMrv },
  { key: "cbam", label: "CBAM", component: Cbam },
  { key: "credits", label: "Credit sourcing", component: Credits },
  { key: "verification", label: "Verification", component: Verification },
  { key: "trading", label: "Trading", component: Trading },
  { key: "india", label: "India CCTS", component: IndiaCcts },
];

export default function App() {
  const { token, user, tenant, loading, logout } = useAuth();
  const [active, setActive] = useState("overview");

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-400 text-sm">Loading…</div>;
  }
  if (!token || !user) {
    return <Login />;
  }

  const ActiveComponent = TABS.find((t) => t.key === active)?.component ?? Overview;

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Carbon Compliance &amp; Trading Platform</h1>
            <p className="text-xs text-slate-400">EU ETS · Shipping MRV · CBAM · Credit sourcing · Verification · Trading · India CCTS</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-sm font-medium text-slate-800">{tenant?.name}</div>
              <div className="text-xs text-slate-400">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200"
            >
              Log out
            </button>
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
