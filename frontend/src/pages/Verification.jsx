import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

export default function Verification() {
  const { data: records, reload } = useApi("/verification/records");
  const { data: orgs } = useApi("/orgs");
  const [busyId, setBusyId] = useState(null);
  const [err, setErr] = useState(null);

  const orgName = (id) => orgs?.find((o) => o.id === id)?.name ?? `#${id}`;

  async function decide(record, approve) {
    setBusyId(record.id);
    setErr(null);
    try {
      await api.post("/verification/decide", {
        subject_type: record.subject_type,
        subject_id: record.subject_id,
        verifier_org_id: record.verifier_org_id,
        approve,
        findings: approve ? "Reviewed and confirmed against source records" : "Discrepancy found — see monitoring data",
      });
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
        <h2 className="text-xl font-bold text-slate-900">Verification (MRV audit)</h2>
        <p className="text-sm text-slate-500 mt-1">
          One cross-cutting stage → verify → commit workflow shared by shipping emission reports, installation
          compliance, and credit-unit issuance — generalizing the cadt staged-write pattern.
        </p>
      </div>
      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <Card title="Verification queue">
        <Table
          columns={[
            { key: "subject_type", label: "Subject" },
            { key: "subject_id", label: "Record ID" },
            { key: "verifier", label: "Verifier" },
            { key: "status", label: "Status" },
            { key: "findings", label: "Findings" },
            { key: "action", label: "" },
          ]}
          rows={records ?? []}
          renderCell={(row, key) => {
            if (key === "subject_type") return row.subject_type.replace(/_/g, " ");
            if (key === "verifier") return orgName(row.verifier_org_id);
            if (key === "status") return <Badge status={row.status} />;
            if (key === "findings") return row.findings ?? "—";
            if (key === "action") {
              if (row.status !== "pending") return null;
              const busy = busyId === row.id;
              return (
                <div className="flex gap-2">
                  <Button variant="primary" disabled={busy} onClick={() => decide(row, true)}>
                    Approve
                  </Button>
                  <Button variant="danger" disabled={busy} onClick={() => decide(row, false)}>
                    Flag non-conformance
                  </Button>
                </div>
              );
            }
            return row[key];
          }}
        />
      </Card>
    </div>
  );
}
