import { useState } from "react";
import { useAuth } from "../auth";

const DEMO_ACCOUNTS = [
  { label: "EU ETS operator — Nordic Steelworks", email: "demo@nordic-steelworks-ab.example" },
  { label: "Shipping — Hanseatic Container Lines", email: "demo@hanseatic-container-lines.example" },
  { label: "CBAM declarant — Iberia Metals Import", email: "demo@iberia-metals-import-sl.example" },
  { label: "Trader — Meridian Carbon Trading", email: "demo@meridian-carbon-trading-llp.example" },
  { label: "Verifier — TransEuro Verification Bureau", email: "demo@transeuro-verification-bureau.example" },
];

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [tenantName, setTenantName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("demo1234");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(tenantName, email, password);
      }
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-xl font-bold text-slate-900">Carbon Compliance &amp; Trading Platform</h1>
          <p className="text-sm text-slate-500 mt-1">Multi-tenant demo — each company is its own tenant.</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-1.5 rounded-lg text-sm font-medium ${mode === "login" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
            >
              Log in
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-1.5 rounded-lg text-sm font-medium ${mode === "register" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
            >
              New tenant
            </button>
          </div>

          <form onSubmit={submit} className="space-y-3">
            {mode === "register" && (
              <div>
                <label className="block text-xs text-slate-500 mb-1">Company / tenant name</label>
                <input
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  required
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="Acme Industrials"
                />
              </div>
            )}
            <div>
              <label className="block text-xs text-slate-500 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
                placeholder="demo@nordic-steelworks-ab.example"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}
            <button
              type="submit"
              disabled={busy}
              className="w-full bg-slate-900 text-white rounded-lg py-2 text-sm font-medium hover:bg-slate-700 disabled:opacity-40"
            >
              {mode === "login" ? "Log in" : "Create tenant"}
            </button>
          </form>
        </div>

        {mode === "login" && (
          <div className="mt-4 bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Demo accounts (password: demo1234)</div>
            <div className="space-y-1">
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.email}
                  onClick={() => setEmail(a.email)}
                  className="w-full text-left text-sm px-2 py-1.5 rounded-lg hover:bg-slate-50 flex justify-between"
                >
                  <span className="text-slate-700">{a.label}</span>
                  <span className="text-slate-400">use</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
