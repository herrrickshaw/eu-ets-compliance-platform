import { useApi } from "../hooks";
import { Card, Stat, Badge } from "../components/ui";

export default function Overview() {
  const { data: compliance } = useApi("/ets/compliance");
  const { data: reports } = useApi("/shipping/emission-reports");
  const { data: declarations } = useApi("/cbam/declarations");
  const { data: units } = useApi("/credits/units");
  const { data: pendingVerif } = useApi("/verification/records?status=pending");
  const { data: prices } = useApi("/trading/prices/1");
  const { data: trades } = useApi("/trading/trades");

  const compliant = compliance?.filter((c) => c.status === "compliant").length ?? 0;
  const shortCount = compliance?.filter((c) => c.status === "short" || c.status === "penalized").length ?? 0;
  const totalEmissions = compliance?.reduce((s, c) => s + c.verified_emissions_t, 0) ?? 0;
  const latestEua = prices?.length ? prices[prices.length - 1].price_eur : null;
  const totalCbamEmissions = declarations?.reduce((s, d) => s + d.total_embedded_emissions_t, 0) ?? 0;
  const retiredCredits = units?.filter((u) => u.status === "retired").reduce((s, u) => s + u.quantity, 0) ?? 0;
  const issuedCredits = units?.reduce((s, u) => s + u.quantity, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Platform overview</h2>
        <p className="text-sm text-slate-500 mt-1">
          Illustrative/sample data — not live regulatory or market feeds. Models reference the EU Union Registry,
          THETIS-MRV, the CBAM Transitional Registry, and the CAD Trust (cadt) credit hierarchy.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <Stat label="EU ETS installations compliant" value={compliant} sub={`${shortCount} short / penalized`} tone={shortCount ? "amber" : "green"} />
        </Card>
        <Card>
          <Stat label="Verified installation emissions (t)" value={Math.round(totalEmissions).toLocaleString()} />
        </Card>
        <Card>
          <Stat label="Latest EUA price" value={latestEua ? `€${latestEua.toFixed(2)}` : "—"} sub="per allowance" />
        </Card>
        <Card>
          <Stat label="Pending verifications" value={pendingVerif?.length ?? 0} tone={pendingVerif?.length ? "amber" : "green"} />
        </Card>
        <Card>
          <Stat label="Shipping emission reports" value={reports?.length ?? 0} sub={`${reports?.filter((r) => r.status === "doc_issued").length ?? 0} with Document of Compliance`} />
        </Card>
        <Card>
          <Stat label="CBAM embedded emissions (t CO2e)" value={Math.round(totalCbamEmissions).toLocaleString()} sub={`${declarations?.length ?? 0} declarations`} />
        </Card>
        <Card>
          <Stat label="Credit units issued" value={Math.round(issuedCredits).toLocaleString()} sub={`${Math.round(retiredCredits).toLocaleString()} retired`} />
        </Card>
        <Card>
          <Stat label="Trades executed" value={trades?.length ?? 0} />
        </Card>
      </div>

      <Card title="Compliance status by installation">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-200">
              <th className="py-2 pr-4">Installation</th>
              <th className="py-2 pr-4">Year</th>
              <th className="py-2 pr-4">Verified (t)</th>
              <th className="py-2 pr-4">Surrendered (t)</th>
              <th className="py-2 pr-4">Deadline</th>
              <th className="py-2 pr-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {(compliance ?? []).map((c) => (
              <tr key={c.id} className="border-b border-slate-100">
                <td className="py-2 pr-4">Installation #{c.installation_id}</td>
                <td className="py-2 pr-4">{c.year}</td>
                <td className="py-2 pr-4">{c.verified_emissions_t.toLocaleString()}</td>
                <td className="py-2 pr-4">{c.allowances_surrendered_t.toLocaleString()}</td>
                <td className="py-2 pr-4">{c.surrender_deadline}</td>
                <td className="py-2 pr-4">
                  <Badge status={c.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
