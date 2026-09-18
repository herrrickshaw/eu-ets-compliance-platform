import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

const INTEGRITY_CATEGORY_LABELS = {
  integrity_controversy: "The Verra REDD+ 'phantom credits' controversy (2023, contested)",
  integrity_response: "The market's response: ICVCM Core Carbon Principles",
};

function formatIntegrityValue(row) {
  if (row.value == null) return "—";
  if (row.unit.startsWith("%")) return `${row.value}%`;
  if (row.unit === "million credits") return `${row.value}M`;
  return `${row.value.toLocaleString()} ${row.unit}`;
}

export default function Verification() {
  const { data: records, reload } = useApi("/verification/records");
  const { data: orgs } = useApi("/orgs");
  const { data: integrityStats } = useApi("/verification/integrity-stats");
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

      <Card title="Why verification matters — a real-world integrity failure, and the market's fix">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 mb-4">
          <strong>Contested, not settled:</strong> in Jan 2023, a joint Guardian/Die Zeit/SourceMaterial
          investigation alleged that {">"}90% of Verra's rainforest (REDD+) offset credits were "phantom
          credits" with little real climate benefit — a landmark case study in why a verification/audit
          stage exists at all, and a reminder that third-party accreditation alone doesn't guarantee
          integrity. Verra publicly disputes the investigation's framing (see the row below) — both sides
          are shown, not a verdict.
        </div>
        <Table
          columns={[
            { key: "category", label: "Category" },
            { key: "metric_label", label: "Metric" },
            { key: "period", label: "Period" },
            { key: "value", label: "Value" },
            { key: "confidence", label: "" },
          ]}
          rows={integrityStats ?? []}
          renderCell={(row, key) => {
            if (key === "category") return INTEGRITY_CATEGORY_LABELS[row.category] ?? row.category;
            if (key === "value") return formatIntegrityValue(row);
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-row notes</summary>
          <ul className="mt-2 space-y-2">
            {(integrityStats ?? [])
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
