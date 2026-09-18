import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

export default function EtsCore() {
  const { data: installations } = useApi("/ets/installations");
  const { data: accounts } = useApi("/ets/accounts");
  const { data: compliance, reload } = useApi("/ets/compliance");
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
    </div>
  );
}
