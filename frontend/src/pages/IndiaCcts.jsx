import { useMemo, useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge } from "../components/ui";

function DataQualityBanner() {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-900">
      <div className="font-semibold mb-1">Data quality note — read before citing these numbers</div>
      <p>
        Sector notification status, entity counts, and target % ranges below are from a September 2026 research
        pass over BEE/MoEFCC/ICAP and secondary reporting — <strong>not</strong> from a primary gazette text (PIB
        pages blocked automated fetch) and <strong>not</strong> from any local repository (a gazette-notification
        database was checked and confirmed to <em>not</em> contain this data). <strong>Fertilizer's status is
        contested across sources</strong> — treat it as unconfirmed. <strong>Iron &amp; Steel is still a draft</strong>{" "}
        under objection until roughly end-August 2026. No official source publishes obligated-sector emissions or
        CCC demand/supply in tCO2e for India — the calculator below is an explicitly-labeled illustrative model,
        not an official BEE/MoEFCC figure.
      </p>
    </div>
  );
}

function StatusBadge({ status }) {
  return <Badge status={status} />;
}

export default function IndiaCcts() {
  const { data: sectors } = useApi("/india/sectors");
  const { data: activities } = useApi("/india/article6-activities");
  const { data: prices } = useApi("/india/carbon-prices");
  const { data: supplyCapacity } = useApi("/india/supply-capacity");

  const [overrides, setOverrides] = useState({});
  const [demand, setDemand] = useState(null);
  const [gap, setGap] = useState(null);
  const [busy, setBusy] = useState(false);
  const [gapBusy, setGapBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [gapErr, setGapErr] = useState(null);

  function setOverride(sectorId, field, value) {
    setOverrides((prev) => ({
      ...prev,
      [sectorId]: { ...prev[sectorId], [field]: value === "" ? undefined : Number(value) },
    }));
  }

  async function runModel() {
    setBusy(true);
    setErr(null);
    try {
      const payload = {
        overrides: Object.entries(overrides).map(([sector_id, v]) => ({
          sector_id: Number(sector_id),
          volume_mt: v.volume_mt,
          intensity_tco2_per_t: v.intensity_tco2_per_t,
        })),
      };
      const result = await api.post("/india/demand-model", payload);
      setDemand(result);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function runGapAnalysis() {
    setGapBusy(true);
    setGapErr(null);
    try {
      const payload = {
        overrides: Object.entries(overrides).map(([sector_id, v]) => ({
          sector_id: Number(sector_id),
          volume_mt: v.volume_mt,
          intensity_tco2_per_t: v.intensity_tco2_per_t,
        })),
      };
      const result = await api.post("/india/gap-analysis", payload);
      setGap(result);
    } catch (e) {
      setGapErr(e.message);
    } finally {
      setGapBusy(false);
    }
  }

  const demandBySector = useMemo(() => {
    const m = {};
    (demand?.sectors ?? []).forEach((s) => (m[s.sector_id] = s));
    return m;
  }, [demand]);

  const activityNameById = useMemo(() => {
    const m = {};
    (activities ?? []).forEach((a) => (m[a.id] = a.name));
    return m;
  }, [activities]);

  const mitigationActivities = activities?.filter((a) => a.category === "mitigation") ?? [];
  const otherActivities = activities?.filter((a) => a.category !== "mitigation") ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">India: CCTS demand vs. Article 6.2 supply</h2>
        <p className="text-sm text-slate-500 mt-1">
          Obligated-sector GHG Emission Intensity (GEI) targets under India's Carbon Credit Trading Scheme
          (demand side) against Article 6.2-eligible activities (supply side), with comparable Asian
          compliance-carbon pricing for context.
        </p>
      </div>

      <DataQualityBanner />

      <Card title="Obligated sectors — GEI targets (demand side)">
        <Table
          columns={[
            { key: "name", label: "Sector" },
            { key: "status", label: "Status" },
            { key: "notification_ref", label: "Notification" },
            { key: "entities", label: "Entities" },
            { key: "target", label: "Target reduction (avg)" },
            { key: "confidence", label: "Confidence" },
          ]}
          rows={sectors ?? []}
          renderCell={(row, key) => {
            if (key === "status") return <StatusBadge status={row.status} />;
            if (key === "notification_ref")
              return row.notification_ref ? `${row.notification_ref}${row.notification_date ? ` (${row.notification_date})` : ""}` : "—";
            if (key === "entities") return row.obligated_entities_est ?? "shared count, not broken out";
            if (key === "target")
              return row.target_reduction_pct_avg != null ? `${row.target_reduction_pct_avg}%` : "not published";
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-sector source notes</summary>
          <ul className="mt-2 space-y-2">
            {(sectors ?? []).map((s) => (
              <li key={s.id}>
                <span className="font-medium text-slate-600">{s.name}:</span> {s.source_note}
              </li>
            ))}
          </ul>
        </details>
      </Card>

      <Card title="Illustrative demand-model calculator">
        <p className="text-xs text-slate-500 mb-3">
          baseline_emissions = volume × intensity; illustrative_abatement_pool = baseline_emissions × target
          reduction % — the scale of reduction obligated entities must find, organically or via CCC purchase.
          Edit volume/intensity per sector (defaults are illustrative, not official) and re-run.
        </p>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-200">
                <th className="py-2 pr-4">Sector</th>
                <th className="py-2 pr-4">Volume (Mt/yr)</th>
                <th className="py-2 pr-4">Intensity (tCO2e/t)</th>
                <th className="py-2 pr-4">Target %</th>
                <th className="py-2 pr-4">Baseline emissions (Mt CO2e)</th>
                <th className="py-2 pr-4">Abatement pool (Mt CO2e)</th>
              </tr>
            </thead>
            <tbody>
              {(sectors ?? []).map((s) => {
                const d = demandBySector[s.id];
                return (
                  <tr key={s.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4">{s.name}</td>
                    <td className="py-2 pr-4">
                      <input
                        type="number"
                        defaultValue={s.default_volume_mt}
                        onChange={(e) => setOverride(s.id, "volume_mt", e.target.value)}
                        className="w-24 border border-slate-300 rounded px-2 py-1 text-sm"
                      />
                    </td>
                    <td className="py-2 pr-4">
                      <input
                        type="number"
                        defaultValue={s.default_intensity_tco2_per_t}
                        onChange={(e) => setOverride(s.id, "intensity_tco2_per_t", e.target.value)}
                        className="w-24 border border-slate-300 rounded px-2 py-1 text-sm"
                      />
                    </td>
                    <td className="py-2 pr-4">{s.target_reduction_pct_avg != null ? `${s.target_reduction_pct_avg}%` : "—"}</td>
                    <td className="py-2 pr-4 text-slate-500">{d ? d.baseline_emissions_mt_co2e.toLocaleString() : "—"}</td>
                    <td className="py-2 pr-4 font-medium text-slate-800">
                      {d ? d.illustrative_abatement_pool_mt_co2e.toLocaleString() : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center gap-4">
          <button
            onClick={runModel}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-40"
          >
            Run demand model
          </button>
          {demand && (
            <div className="text-sm">
              Total illustrative demand: <span className="font-bold">{demand.total_illustrative_demand_mt_co2e.toLocaleString()} Mt CO2e</span>
            </div>
          )}
        </div>
        {err && <div className="text-sm text-rose-600 mt-2">{err}</div>}
        {demand && <p className="text-xs text-slate-400 mt-2">{demand.methodology_note}</p>}
      </Card>

      <Card title="Supply capacity by activity (MNRE / MoPNG / PIB / CEA / BEE)">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          No official Article 6.2 pipeline volume (tCO2e) is published for India, so this is a bottom-up proxy:
          capacity/target figures per eligible activity from primary ministry sources, converted to potential
          avoided tCO2e/year where a defensible physical conversion exists.{" "}
          <strong>aspirational_target</strong> = a policy goal (e.g. 2030), not yet built —{" "}
          <strong>awarded_operational</strong> = capacity actually awarded/under construction/running —{" "}
          <strong>current_actual</strong> = a measured to-date figure. Don't sum these as if they were all
          available today.
        </div>
        {(supplyCapacity ?? []).length === 0 ? (
          <div className="text-sm text-slate-400 py-4 text-center">No supply-capacity data seeded yet.</div>
        ) : (
          <Table
            columns={[
              { key: "activity", label: "Activity" },
              { key: "metric_label", label: "Metric" },
              { key: "value", label: "Figure" },
              { key: "figure_type", label: "Type" },
              { key: "potential", label: "Potential avoided (Mt CO2e/yr)" },
              { key: "source", label: "Source" },
            ]}
            rows={supplyCapacity ?? []}
            renderCell={(row, key) => {
              if (key === "activity") return activityNameById[row.activity_id] ?? `#${row.activity_id}`;
              if (key === "value") return row.value != null ? `${row.value.toLocaleString()} ${row.unit}` : "no figure found";
              if (key === "figure_type") return <Badge status={row.figure_type === "aspirational_target" ? "pending" : "compliant"} label={row.figure_type} />;
              if (key === "potential")
                return row.potential_avoided_mt_co2e != null ? row.potential_avoided_mt_co2e.toLocaleString() : "not quantifiable";
              if (key === "source")
                return row.source_url ? (
                  <a href={row.source_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                    {row.source_name}
                  </a>
                ) : (
                  row.source_name
                );
              return row[key];
            }}
          />
        )}
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Conversion methodology per row</summary>
          <ul className="mt-2 space-y-2">
            {(supplyCapacity ?? []).map((r) => (
              <li key={r.id}>
                <span className="font-medium text-slate-600">
                  {activityNameById[r.activity_id]} — {r.metric_label}:
                </span>{" "}
                {r.conversion_note ?? "no conversion — excluded from gap-analysis total"}
              </li>
            ))}
          </ul>
        </details>
      </Card>

      <Card title="Demand vs. supply gap analysis">
        <p className="text-xs text-slate-500 mb-3">
          Compares the illustrative CCTS demand model above against the supply capacity table, split into
          near-term (awarded/operational/current, comparable to the FY2025-27 compliance window) and
          long-range aspirational (2030/2050 policy targets — an upper bound, not available supply today).
          Uses your current volume/intensity overrides if you've edited them above.
        </p>
        <button
          onClick={runGapAnalysis}
          disabled={gapBusy}
          className="px-3 py-1.5 rounded-lg text-sm font-medium bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-40"
        >
          Run gap analysis
        </button>
        {gapErr && <div className="text-sm text-rose-600 mt-2">{gapErr}</div>}
        {gap && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-slate-500">Total demand (CCTS, FY2025-27)</div>
                <div className="text-xl font-bold">{gap.total_demand_mt_co2e.toLocaleString()} Mt CO2e</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Near-term supply (awarded/actual)</div>
                <div className="text-xl font-bold">{gap.total_near_term_supply_mt_co2e.toLocaleString()} Mt CO2e</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">
                  {gap.near_term_gap_mt_co2e >= 0 ? "Near-term demand exceeds supply by" : "Near-term supply exceeds demand by"}
                </div>
                <div className={`text-xl font-bold ${gap.near_term_gap_mt_co2e >= 0 ? "text-rose-600" : "text-emerald-600"}`}>
                  {Math.abs(gap.near_term_gap_mt_co2e).toLocaleString()} Mt CO2e
                </div>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-900">
              <strong>Long-range aspirational potential (2030, mostly): {gap.total_aspirational_supply_mt_co2e.toLocaleString()} Mt CO2e</strong>{" "}
              — dominated by the 30 GW offshore wind target (78.4 Mt) and the 5 MMT green hydrogen target (47.5 Mt).
              This is {(gap.total_aspirational_supply_mt_co2e / gap.total_demand_mt_co2e).toFixed(1)}x current demand
              on paper, but reflects policy goals with little built capacity behind them yet (e.g. India's first
              offshore wind tender drew zero bids) — not a claim that supply will actually outpace demand.
            </div>
            {gap.supply_rows_excluded_no_conversion.length > 0 && (
              <details className="text-xs text-slate-500">
                <summary className="cursor-pointer hover:text-slate-700">
                  Excluded from both totals — no defensible conversion or wrong time horizon ({gap.supply_rows_excluded_no_conversion.length})
                </summary>
                <ul className="mt-2 space-y-1">
                  {gap.supply_rows_excluded_no_conversion.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </details>
            )}
            <p className="text-xs text-slate-400">{gap.supply_methodology_note}</p>
          </div>
        )}
      </Card>

      <Card title="Article 6.2 eligible activities (full list)">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Mitigation ({mitigationActivities.length})</div>
            <ul className="space-y-1 text-sm">
              {mitigationActivities.map((a) => (
                <li key={a.id} className="flex items-center gap-2">
                  <span className="text-slate-700">{a.name}</span>
                  {a.also_ccts_offset_eligible && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">also offset-eligible</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Alternate materials &amp; removal</div>
            <ul className="space-y-1 text-sm">
              {otherActivities.map((a) => (
                <li key={a.id} className="flex items-center gap-2">
                  <span className="text-slate-700">{a.name}</span>
                  <span className="text-xs text-slate-400">({a.category.replace(/_/g, " ")})</span>
                  {a.also_ccts_offset_eligible && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-600">also offset-eligible</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      <Card title="Comparable compliance-carbon pricing (Korea, China, Japan, EU)">
        <Table
          columns={[
            { key: "market", label: "Market" },
            { key: "instrument", label: "Instrument" },
            { key: "price", label: "Price" },
            { key: "usd", label: "≈ USD/t" },
            { key: "date", label: "As of" },
            { key: "confidence", label: "" },
          ]}
          rows={prices ?? []}
          renderCell={(row, key) => {
            if (key === "price") {
              const native = row.price_native_high
                ? `${row.price_native.toLocaleString()}–${row.price_native_high.toLocaleString()} ${row.currency}`
                : `${row.price_native.toLocaleString()} ${row.currency}`;
              return native;
            }
            if (key === "usd") {
              if (row.price_usd) return `$${row.price_usd.toFixed(2)}`;
              return row.price_native_high ? "n/a — policy corridor, not a traded price" : "n/a";
            }
            if (key === "date") return row.price_date;
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Trend notes</summary>
          <ul className="mt-2 space-y-2">
            {(prices ?? []).map((p) => (
              <li key={p.id}>
                <span className="font-medium text-slate-600">
                  {p.market} — {p.instrument}:
                </span>{" "}
                {p.trend_note}
              </li>
            ))}
          </ul>
        </details>
      </Card>
    </div>
  );
}
