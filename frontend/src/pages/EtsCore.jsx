import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

const SYSTEM_STAT_CATEGORY_LABELS = {
  system_scale: "System scale",
  allocation: "Allocation (auction vs. free)",
  market_stability_reserve: "Market Stability Reserve",
  compliance: "Compliance & penalties",
};

function formatSystemStatValue(row) {
  if (row.value == null) return "—";
  if (row.unit === "Mt CO2e") return `${row.value.toLocaleString()} Mt`;
  if (row.unit.startsWith("%")) return `${row.value}%`;
  if (row.unit === "EUR/tCO2e") return `€${row.value}/t`;
  return `${row.value.toLocaleString()} ${row.unit}`;
}

export default function EtsCore() {
  const { data: installations } = useApi("/ets/installations");
  const { data: accounts } = useApi("/ets/accounts");
  const { data: compliance, reload } = useApi("/ets/compliance");
  const { data: systemStats } = useApi("/ets/system-stats");
  const [busyId, setBusyId] = useState(null);
  const [err, setErr] = useState(null);

  const installName = (id) => installations?.find((i) => i.id === id)?.name ?? `#${id}`;
  const accountBalance = (installationId) =>
    accounts?.find((a) => a.installation_id === installationId && a.account_type === "operator_holding")?.balance;

  async function surrenderShortfall(row) {
    const shortfall = Math.max(0, row.verified_emissions_t - row.allowances_surrendered_t);
    if (shortfall <= 0) return;
    setBusyId(row.id);
    setErr(null);
    try {
      await api.post("/ets/surrender", { installation_id: row.installation_id, year: row.year, amount_t: shortfall });
      reload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">EU ETS core</h2>
        <p className="text-sm text-slate-500 mt-1">
          Installation allowance accounts and annual compliance, modeled on the EU Union Registry's operator
          holding account / surrender workflow.
        </p>
      </div>

      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <Card title="Installations & EUA holding balance">
        <Table
          columns={[
            { key: "name", label: "Installation" },
            { key: "sector", label: "Sector" },
            { key: "country", label: "Country" },
            { key: "ets_scheme", label: "Scheme" },
            { key: "balance", label: "EUA balance held" },
          ]}
          rows={installations ?? []}
          renderCell={(row, key) => (key === "balance" ? (accountBalance(row.id) ?? 0).toLocaleString() : row[key])}
        />
      </Card>

      <Card title="Compliance & surrender">
        <Table
          columns={[
            { key: "installation", label: "Installation" },
            { key: "year", label: "Year" },
            { key: "verified_emissions_t", label: "Verified emissions (t)" },
            { key: "allowances_surrendered_t", label: "Surrendered (t)" },
            { key: "surrender_deadline", label: "Deadline" },
            { key: "status", label: "Status" },
            { key: "action", label: "" },
          ]}
          rows={compliance ?? []}
          renderCell={(row, key) => {
            if (key === "installation") return installName(row.installation_id);
            if (key === "status") return <Badge status={row.status} />;
            if (key === "action") {
              const shortfall = row.verified_emissions_t - row.allowances_surrendered_t;
              if (shortfall <= 0) return <span className="text-emerald-600 text-xs">Fully surrendered</span>;
              return (
                <Button variant="ghost" disabled={busyId === row.id} onClick={() => surrenderShortfall(row)}>
                  Surrender {Math.round(shortfall).toLocaleString()} t
                </Button>
              );
            }
            return row[key]?.toLocaleString?.() ?? row[key];
          }}
        />
      </Card>

      <Card title="The EU ETS at full scale — next to this 3-installation demo">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          The tables above model 3 demo installations. The real system covers ~35% of all EU GHG
          emissions across ~8,700 currently-active stationary installations, ~390 aircraft operators, and
          ~3,300 shipping companies. Sourced via{" "}
          <a className="underline" href="https://icapcarbonaction.com/en/ets/eu-emissions-trading-system-eu-ets" target="_blank" rel="noreferrer">
            ICAP's EU ETS policy summary
          </a>{" "}
          and the{" "}
          <a
            className="underline"
            href="https://www.eea.europa.eu/en/analysis/maps-and-charts/emissions-trading-viewer-1-dashboards"
            target="_blank"
            rel="noreferrer"
          >
            European Environment Agency's data viewer
          </a>
          , both via search/WebFetch summarization rather than a primary document read page-by-page this
          session — marked secondary throughout, not inflated to primary.
        </div>
        <Table
          columns={[
            { key: "category", label: "Category" },
            { key: "metric_label", label: "Metric" },
            { key: "period", label: "Period" },
            { key: "value", label: "Value" },
            { key: "confidence", label: "" },
          ]}
          rows={systemStats ?? []}
          renderCell={(row, key) => {
            if (key === "category") return SYSTEM_STAT_CATEGORY_LABELS[row.category] ?? row.category;
            if (key === "value") return formatSystemStatValue(row);
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-row notes</summary>
          <ul className="mt-2 space-y-2">
            {(systemStats ?? [])
              .filter((r) => r.notes)
              .map((r) => (
                <li key={r.id}>
                  <strong>{r.metric_label}:</strong> {r.notes}
                </li>
              ))}
          </ul>
        </details>
      </Card>
    </div>
  );
}
