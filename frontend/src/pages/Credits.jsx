import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

const DEMO_BUYER_ORG_ID = 10; // Meridian Carbon Trading LLP

export default function Credits() {
  const { data: projects } = useApi("/credits/projects");
  const { data: units, reload } = useApi("/credits/units");
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
