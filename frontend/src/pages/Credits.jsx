import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

const DEMO_BUYER_ORG_ID = 10; // Meridian Carbon Trading LLP

const MARKET_CATEGORY_LABELS = {
  compliance_market: "Global compliance markets (mandatory cap-and-trade)",
  vcm_headline: "Voluntary carbon market (VCM) — headline",
  vcm_category_share: "VCM — share by project category",
  context: "Context (VCM vs. compliance, calculated)",
};

function formatStatValue(row) {
  if (row.value == null) return "—";
  if (row.unit === "USD billion") return `$${row.value.toLocaleString()}B`;
  if (row.unit === "USD million") return `$${row.value.toLocaleString()}M`;
  if (row.unit === "Gt CO2e") return `${row.value} Gt`;
  if (row.unit === "Mt CO2e") return `${row.value.toLocaleString()} Mt`;
  if (row.unit === "USD/tCO2e") return `$${row.value}/t`;
  if (row.unit.startsWith("%")) return `${row.value}%`;
  return `${row.value.toLocaleString()} ${row.unit}`;
}

export default function Credits() {
  const { data: projects } = useApi("/credits/projects");
  const { data: units, reload } = useApi("/credits/units");
  const { data: marketStats } = useApi("/credits/global-market-stats");
  const [busyId, setBusyId] = useState(null);
  const [err, setErr] = useState(null);

  const projectName = (issuanceProjectId) => projects?.find((p) => p.id === issuanceProjectId)?.name;

  async function purchase(unitId) {
    setBusyId(unitId);
    setErr(null);
    try {
      await api.post(`/credits/units/${unitId}/purchase`, { unit_id: unitId, buyer_org_id: DEMO_BUYER_ORG_ID });
      reload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusyId(null);
    }
  }

  async function retire(unitId) {
    setBusyId(unitId);
    setErr(null);
    try {
      await api.post(`/credits/units/${unitId}/retire`, {});
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
        <h2 className="text-xl font-bold text-slate-900">Carbon credit sourcing</h2>
        <p className="text-sm text-slate-500 mt-1">
          Project/issuance/unit hierarchy modeled on Chia-Network/cadt (Climate Action Data Trust): units move
          staged → issued → held → retired, so a unit is only tradeable once it has cleared verification.
        </p>
      </div>
      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <Card title="How big is the global carbon-credit market, and who has the share?">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          <strong>Compliance markets (EU ETS, China ETS, etc.) dwarf the voluntary carbon market</strong> —
          roughly three orders of magnitude bigger by value. The EU ETS alone is ~85% of global
          compliance-market VALUE despite covering only ~40% of global compliance VOLUME, because EUAs
          trade around $80/tCO2e versus China's ~$11/tCO2e. VCM rows below are primary (
          <a
            className="underline"
            href="https://www.ecosystemmarketplace.com/publications/2025-state-of-the-voluntary-carbon-market-sovcm/"
            target="_blank"
            rel="noreferrer"
          >
            Ecosystem Marketplace's State of the Voluntary Carbon Market 2025
          </a>
          , read directly); compliance-market rows are secondary (World Bank State and Trends of Carbon
          Pricing 2025, via search synthesis) — confidence is marked honestly per row, not uniformly.
        </div>
        <Table
          columns={[
            { key: "category", label: "Category" },
            { key: "metric_label", label: "Metric" },
            { key: "period", label: "Period" },
            { key: "value", label: "Value" },
            { key: "confidence", label: "" },
          ]}
          rows={marketStats ?? []}
          renderCell={(row, key) => {
            if (key === "category") return MARKET_CATEGORY_LABELS[row.category] ?? row.category;
            if (key === "value") return formatStatValue(row);
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-row notes</summary>
          <ul className="mt-2 space-y-2">
            {(marketStats ?? [])
              .filter((r) => r.notes)
              .map((r) => (
                <li key={r.id}>
                  <strong>{r.metric_label}:</strong> {r.notes}
                </li>
              ))}
          </ul>
        </details>
      </Card>

      <Card title="Registered projects">
        <Table
          columns={[
            { key: "name", label: "Project" },
            { key: "country", label: "Country" },
            { key: "status", label: "Status" },
          ]}
          rows={projects ?? []}
          renderCell={(row, key) => (key === "status" ? <Badge status={row.status} /> : row[key])}
        />
      </Card>

      <Card title="Credit units">
        <Table
          columns={[
            { key: "id", label: "Unit batch" },
            { key: "quantity", label: "Quantity (tCO2e)" },
            { key: "status", label: "Status" },
            { key: "action", label: "" },
          ]}
          rows={units ?? []}
          renderCell={(row, key) => {
            if (key === "id") return `#${row.id}`;
            if (key === "quantity") return row.quantity.toLocaleString();
            if (key === "status") return <Badge status={row.status} />;
            if (key === "action") {
              const busy = busyId === row.id;
              if (row.status === "issued")
                return (
                  <Button variant="ghost" disabled={busy} onClick={() => purchase(row.id)}>
                    Buy for Meridian Carbon Trading
                  </Button>
                );
              if (row.status === "held")
                return (
                  <Button variant="danger" disabled={busy} onClick={() => retire(row.id)}>
                    Retire
                  </Button>
                );
              if (row.status === "staged") return <span className="text-xs text-amber-600">Awaiting verification</span>;
              return null;
            }
            return row[key];
          }}
        />
      </Card>
    </div>
  );
}
