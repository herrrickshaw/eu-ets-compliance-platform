import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";

export default function Cbam() {
  const { data: declarants } = useApi("/cbam/declarants");
  const { data: defaults } = useApi("/cbam/default-values");
  const { data: imports } = useApi("/cbam/imports");
  const { data: declarations, reload } = useApi("/cbam/declarations");
  const { data: phaseInSchedule } = useApi("/cbam/phase-in-schedule");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const [analysisYear, setAnalysisYear] = useState(2026);
  const [analysis, setAnalysis] = useState(null);
  const [projection, setProjection] = useState(null);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [analysisErr, setAnalysisErr] = useState(null);

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

  async function runDemandAnalysis() {
    setAnalysisBusy(true);
    setAnalysisErr(null);
    try {
      const [a, p] = await Promise.all([
        api.get(`/cbam/demand-analysis?year=${analysisYear}`),
        api.get(`/cbam/demand-projection?base_year=${analysisYear}`),
      ]);
      setAnalysis(a);
      setProjection(p);
    } catch (e) {
      setAnalysisErr(e.message);
    } finally {
      setAnalysisBusy(false);
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

      <Card title="Certificate demand & phase-in ramp (not a supply-demand gap)">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          CBAM certificates aren't volume-capped like EUAs or voluntary carbon credits — the EU sells as
          many as a declarant needs, priced weekly off the EUA auction average. So there's no scarcity-driven
          supply-vs-demand gap here. The real gap is <strong>temporal</strong>: free allocation to the
          equivalent EU ETS sector phases out 2026→2034 (Reg. (EU) 2023/956 Art. 31(a), amended by the
          Omnibus Regulation (EU) 2025/2083), so only a rising share of your embedded emissions actually
          requires a surrendered certificate today — the rest is deferred liability that lands as the
          phase-in advances.
        </div>
        <Table
          columns={[
            { key: "year", label: "Year" },
            { key: "free_allocation_pct", label: "Free allocation remaining" },
            { key: "cbam_factor_pct", label: "CBAM factor (certificate obligation)" },
            { key: "note", label: "Note" },
          ]}
          rows={phaseInSchedule ?? []}
          renderCell={(row, key) => {
            if (key === "free_allocation_pct" || key === "cbam_factor_pct") return `${row[key]}%`;
            if (key === "note") return row.note ?? "—";
            return row[key];
          }}
        />
        <div className="mt-4 flex items-end gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Base year (uses your declared imports for that year)</label>
            <select
              value={analysisYear}
              onChange={(e) => setAnalysisYear(Number(e.target.value))}
              className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm"
            >
              {(phaseInSchedule ?? []).map((s) => (
                <option key={s.year} value={s.year}>
                  {s.year}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={runDemandAnalysis} disabled={analysisBusy}>
            Run demand analysis
          </Button>
        </div>
        {analysisErr && <div className="text-sm text-rose-600 mt-2">{analysisErr}</div>}
        {analysis && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-slate-500">Full eventual liability</div>
                <div className="text-lg font-bold">{analysis.total_embedded_emissions_t.toLocaleString()} t</div>
                {analysis.full_liability_cost_eur != null && (
                  <div className="text-xs text-slate-400">€{analysis.full_liability_cost_eur.toLocaleString()}</div>
                )}
              </div>
              <div>
                <div className="text-xs text-slate-500">Actual obligation this year ({analysis.cbam_factor_pct}%)</div>
                <div className="text-lg font-bold">{analysis.actual_obligation_t.toLocaleString()} t</div>
                {analysis.actual_obligation_cost_eur != null && (
                  <div className="text-xs text-slate-400">€{analysis.actual_obligation_cost_eur.toLocaleString()}</div>
                )}
              </div>
              <div>
                <div className="text-xs text-slate-500">Deferred liability</div>
                <div className="text-lg font-bold text-amber-600">{analysis.deferred_liability_t.toLocaleString()} t</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Reference price</div>
                <div className="text-lg font-bold">
                  {analysis.reference_price_eur_per_t != null ? `€${analysis.reference_price_eur_per_t}/t` : "n/a"}
                </div>
                <div className="text-xs text-slate-400">{analysis.reference_price_date}</div>
              </div>
            </div>
            {analysis.declarant_count === 0 && (
              <div className="text-sm text-amber-600">
                No declarants belong to your tenant, or no imports were declared in {analysisYear} — figures are zero.
              </div>
            )}
            <p className="text-xs text-slate-400">{analysis.methodology_note}</p>
          </div>
        )}
        {projection && (
          <div className="mt-5 pt-5 border-t border-slate-200">
            <div className="text-xs font-semibold text-slate-500 uppercase mb-2">
              Ramp if {projection.base_year}'s import volume repeats every year
            </div>
            <Table
              columns={[
                { key: "year", label: "Year" },
                { key: "cbam_factor_pct", label: "CBAM factor" },
                { key: "obligation_t", label: "Obligation (t)" },
                { key: "obligation_cost_eur", label: "Cost (€)" },
              ]}
              rows={projection.years}
              renderCell={(row, key) => {
                if (key === "cbam_factor_pct") return `${row[key]}%`;
                if (key === "obligation_t") return row[key].toLocaleString();
                if (key === "obligation_cost_eur") return row[key] != null ? `€${row[key].toLocaleString()}` : "n/a";
                return row[key];
              }}
            />
            <p className="text-xs text-slate-400 mt-2">{projection.note}</p>
          </div>
        )}
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
