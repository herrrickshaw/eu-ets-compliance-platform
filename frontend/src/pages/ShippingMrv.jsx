import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

const COST_CATEGORY_LABELS = {
  aggregate_cost: "Industry-wide aggregate cost (2024, 40% phase-in)",
  context: "Context",
  pass_through: "Pass-through to shippers/passengers",
  route_case_study: "Route case study",
  projection: "Illustrative projection (not official)",
};

function formatCostValue(row) {
  if (row.value == null) return "—";
  if (row.unit.startsWith("EUR million")) return `€${row.value.toLocaleString()}M`;
  if (row.unit.startsWith("EUR per voyage")) return `€${row.value.toLocaleString()}`;
  if (row.unit === "million EUAs") return `${row.value}M EUAs`;
  if (row.unit === "Mt CO2") return `${row.value} Mt`;
  if (row.unit.startsWith("%")) return `${row.value}%`;
  return `${row.value.toLocaleString()} ${row.unit}`;
}

export default function ShippingMrv() {
  const { data: vessels } = useApi("/shipping/vessels");
  const { data: plans } = useApi("/shipping/monitoring-plans");
  const { data: voyages } = useApi("/shipping/voyages");
  const { data: reports, reload } = useApi("/shipping/emission-reports");
  const { data: etsCosts } = useApi("/shipping/ets-compliance-cost");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const vesselName = (id) => vessels?.find((v) => v.id === id)?.name ?? `#${id}`;

  async function generateReport(vesselId, year) {
    setBusy(true);
    setErr(null);
    try {
      await api.post("/shipping/emission-reports/submit", { vessel_id: vesselId, year });
      reload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Shipping MRV</h2>
        <p className="text-sm text-slate-500 mt-1">
          EU ETS maritime extension: voyage fuel data → emission report → verifier sign-off → Document of
          Compliance, following the THETIS-MRV state machine. Intra-EU legs carry 100% ETS exposure, extra-EU
          legs 50% (Art. 3ga MRV Regulation).
        </p>
      </div>
      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <Card title="Fleet">
        <Table
          columns={[
            { key: "name", label: "Vessel" },
            { key: "imo_number", label: "IMO number" },
            { key: "vessel_type", label: "Type" },
            { key: "gross_tonnage", label: "GT" },
            { key: "plan_status", label: "Monitoring plan" },
            { key: "action", label: "" },
          ]}
          rows={vessels ?? []}
          renderCell={(row, key) => {
            if (key === "gross_tonnage") return row.gross_tonnage.toLocaleString();
            if (key === "plan_status") {
              const plan = plans?.find((p) => p.vessel_id === row.id);
              return plan ? <Badge status={plan.status} /> : <Badge status="draft" />;
            }
            if (key === "action")
              return (
                <Button variant="ghost" disabled={busy} onClick={() => generateReport(row.id, 2025)}>
                  Generate 2025 report
                </Button>
              );
            return row[key];
          }}
        />
      </Card>

      <Card title="Emission reports">
        <Table
          columns={[
            { key: "vessel", label: "Vessel" },
            { key: "year", label: "Year" },
            { key: "total_co2_t", label: "Total CO2 (t)" },
            { key: "ets_eligible_co2_t", label: "ETS-eligible CO2 (t)" },
            { key: "status", label: "Status" },
          ]}
          rows={reports ?? []}
          renderCell={(row, key) => {
            if (key === "vessel") return vesselName(row.vessel_id);
            if (key === "status") return <Badge status={row.status} />;
            if (key === "total_co2_t" || key === "ets_eligible_co2_t") return row[key].toLocaleString();
            return row[key];
          }}
        />
      </Card>

      <Card title="What EU ETS compliance actually costs shipping — real 2024 figures">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          Industry-wide figures, distinct from the fleet demo above (which models one tenant's own MRV
          workflow). Sourced primarily from the European Commission's own first monitoring report on the
          ETS maritime extension,{" "}
          <a
            className="underline"
            href="https://climate.ec.europa.eu/document/download/1bb8387b-bdc4-4489-9d76-7ff30239704d_en?filename=First+report+on+the+implementation+of+the+ETS+extension+to+maritime+transport.pdf"
            target="_blank"
            rel="noreferrer"
          >
            COM(2025) 110 final
          </a>{" "}
          (18 Mar 2025). <strong>Headline: ~€2,200M industry-wide cost in 2024 (40% phase-in), a ~3.7%
          increase in total shipping costs</strong>, mostly passed through to shippers/passengers via
          explicit surcharges. 2025 (70% phase-in) and full 2026+ (100%) figures are not yet published —
          the one "projection" row below is this platform's own illustrative extrapolation, not an
          official figure, and is flagged as such.
        </div>
        <Table
          columns={[
            { key: "category", label: "Category" },
            { key: "metric_label", label: "Metric" },
            { key: "period", label: "Period" },
            { key: "value", label: "Value" },
            { key: "confidence", label: "" },
          ]}
          rows={etsCosts ?? []}
          renderCell={(row, key) => {
            if (key === "category") return COST_CATEGORY_LABELS[row.category] ?? row.category;
            if (key === "value") return formatCostValue(row);
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-row notes</summary>
          <ul className="mt-2 space-y-2">
            {(etsCosts ?? [])
              .filter((r) => r.notes)
              .map((r) => (
                <li key={r.id}>
                  <strong>{r.metric_label}:</strong> {r.notes}
                </li>
              ))}
          </ul>
        </details>
      </Card>

      <Card title="Voyage log">
        <Table
          columns={[
            { key: "vessel", label: "Vessel" },
            { key: "route", label: "Route" },
            { key: "distance_nm", label: "Distance (nm)" },
            { key: "fuel_consumed_mt", label: "Fuel (mt)" },
            { key: "intra_eu", label: "Intra-EU" },
          ]}
          rows={voyages ?? []}
          renderCell={(row, key) => {
            if (key === "vessel") return vesselName(row.vessel_id);
            if (key === "route") return `${row.departure_port} → ${row.arrival_port}`;
            if (key === "distance_nm") return row.distance_nm.toLocaleString();
            if (key === "fuel_consumed_mt") return row.fuel_consumed_mt.toFixed(1);
            if (key === "intra_eu") return row.intra_eu ? "Yes (100%)" : "No (50%)";
            return row[key];
          }}
        />
      </Card>
    </div>
  );
}
