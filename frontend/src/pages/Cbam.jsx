import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

export default function Cbam() {
  const { data: declarants } = useApi("/cbam/declarants");
  const { data: defaults } = useApi("/cbam/default-values");
  const { data: imports } = useApi("/cbam/imports");
  const { data: declarations, reload } = useApi("/cbam/declarations");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const declarantEori = (id) => declarants?.find((d) => d.id === id)?.eori_number ?? `#${id}`;

  async function reconcile(declarantId, year, quarter) {
    setBusy(true);
    setErr(null);
    try {
      await api.post(`/cbam/declarations/${declarantId}/${year}/${quarter}/reconcile`, {});
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
        <h2 className="text-xl font-bold text-slate-900">CBAM</h2>
        <p className="text-sm text-slate-500 mt-1">
          Modeled on the CBAM Transitional Registry's three-way split: Trader Portal (declared imports),
          Authorisation Management (declarant status), Data Reconciliation for Monitoring &amp; Control
          (quarterly roll-up vs. certificates held).
        </p>
      </div>
      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <Card title="Authorised declarants">
        <Table
          columns={[
            { key: "eori_number", label: "EORI number" },
            { key: "auth_status", label: "Status" },
          ]}
          rows={declarants ?? []}
          renderCell={(row, key) => (key === "auth_status" ? <Badge status={row.auth_status} /> : row[key])}
        />
      </Card>

      <Card title="Declared imports">
        <Table
          columns={[
            { key: "declarant", label: "Declarant" },
            { key: "good_name", label: "Good" },
            { key: "cn_code", label: "CN code" },
            { key: "country_of_origin", label: "Origin" },
            { key: "quantity_t", label: "Qty (t)" },
            { key: "direct_emissions_t", label: "Direct emissions (t CO2e)" },
            { key: "indirect_emissions_t", label: "Indirect emissions (t CO2e)" },
            { key: "emission_source", label: "Source" },
          ]}
          rows={imports ?? []}
          renderCell={(row, key) => {
            if (key === "declarant") return declarantEori(row.declarant_id);
            if (key === "emission_source") return <Badge status={row.emission_source} />;
            if (key === "quantity_t" || key === "direct_emissions_t" || key === "indirect_emissions_t")
              return row[key].toLocaleString();
            return row[key];
          }}
        />
      </Card>

      <Card title="Quarterly declarations">
        <div className="mb-3 flex gap-2">
          {declarants?.map((d) => (
            <Button key={d.id} variant="ghost" disabled={busy} onClick={() => reconcile(d.id, 2026, 1)}>
              Reconcile Q1 2026 for {d.eori_number}
            </Button>
          ))}
        </div>
        <Table
          columns={[
            { key: "declarant", label: "Declarant" },
            { key: "period", label: "Period" },
            { key: "total_embedded_emissions_t", label: "Total embedded emissions (t)" },
            { key: "certificates_surrendered_t", label: "Certificates surrendered (t)" },
            { key: "status", label: "Status" },
          ]}
          rows={declarations ?? []}
          renderCell={(row, key) => {
            if (key === "declarant") return declarantEori(row.declarant_id);
            if (key === "period") return `Q${row.quarter} ${row.year}`;
            if (key === "status") return <Badge status={row.status} />;
            if (key === "total_embedded_emissions_t" || key === "certificates_surrendered_t")
              return row[key].toLocaleString();
            return row[key];
          }}
        />
      </Card>

      <Card title="Default emission values (reference table)">
        <Table
          columns={[
            { key: "cn_code", label: "CN code" },
            { key: "good_name", label: "Good" },
            { key: "country", label: "Country" },
            { key: "direct_emissions_factor", label: "Direct factor (t/t)" },
            { key: "indirect_emissions_factor", label: "Indirect factor (t/t)" },
            { key: "markup_pct", label: "Mark-up %" },
            { key: "valid_from", label: "Valid from" },
          ]}
          rows={defaults ?? []}
        />
      </Card>
    </div>
  );
}
