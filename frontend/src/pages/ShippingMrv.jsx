import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

export default function ShippingMrv() {
  const { data: vessels } = useApi("/shipping/vessels");
  const { data: plans } = useApi("/shipping/monitoring-plans");
  const { data: voyages } = useApi("/shipping/voyages");
  const { data: reports, reload } = useApi("/shipping/emission-reports");
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
