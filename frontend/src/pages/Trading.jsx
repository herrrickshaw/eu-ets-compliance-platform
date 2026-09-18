import { useState } from "react";
import { useApi } from "../hooks";
import { api } from "../api";
import { Card, Table, Badge, Button } from "../components/ui";
import Sparkline from "../components/Sparkline";

const DEMO_ORG_ID = 10; // Meridian Carbon Trading LLP

const MARKET_REALITY_CATEGORY_LABELS = {
  ice_trading_volume: "ICE trading volume (2024, read directly from source)",
  market_structure: "Market structure & 2025 figures",
  context: "Context — real price vs. this demo",
};

function formatRealityValue(row) {
  if (row.value == null) return "—";
  if (row.unit.startsWith("USD trillion")) return `$${row.value}T+`;
  if (row.unit === "USD billion") return `$${row.value}B`;
  if (row.unit === "million contracts") return `${row.value}M`;
  if (row.unit === "billion allowances" || row.unit === "billion credits") return `${row.value}B`;
  if (row.unit === "EUR/tCO2e") return `€${row.value}/t`;
  return `${row.value.toLocaleString()} ${row.unit}`;
}

export default function Trading() {
  const { data: instruments } = useApi("/trading/instruments");
  const [selected, setSelected] = useState(null);
  const instrumentId = selected ?? instruments?.[0]?.id;

  const { data: prices } = useApi(instrumentId ? `/trading/prices/${instrumentId}` : null, [instrumentId]);
  const { data: orders, reload: reloadOrders } = useApi("/trading/orders?status=open");
  const { data: trades, reload: reloadTrades } = useApi("/trading/trades");
  const { data: positions } = useApi(`/trading/positions?org_id=${DEMO_ORG_ID}`, [instrumentId]);
  const { data: marketReality } = useApi("/trading/market-reality");

  const [side, setSide] = useState("buy");
  const [qty, setQty] = useState(1000);
  const [price, setPrice] = useState(70);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const instrumentSymbol = (id) => instruments?.find((i) => i.id === id)?.symbol ?? `#${id}`;

  async function placeOrder() {
    if (!instrumentId) return;
    setBusy(true);
    setErr(null);
    try {
      await api.post("/trading/orders", {
        org_id: DEMO_ORG_ID,
        instrument_id: instrumentId,
        side,
        quantity: Number(qty),
        limit_price_eur: Number(price),
      });
      reloadOrders();
      reloadTrades();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function cancel(orderId) {
    setBusy(true);
    try {
      await api.del(`/trading/orders/${orderId}`);
      reloadOrders();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Trading</h2>
        <p className="text-sm text-slate-500 mt-1">
          One order book / position ledger shared across EUAs, CBAM certificates, and voluntary credits — same
          accounting spine, different instrument type.
        </p>
      </div>
      {err && <div className="text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">{err}</div>}

      <div className="flex gap-2">
        {instruments?.map((i) => (
          <button
            key={i.id}
            onClick={() => setSelected(i.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border ${
              i.id === instrumentId ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-200"
            }`}
          >
            {i.symbol}
          </button>
        ))}
      </div>

      <Card title={`Price — ${instrumentId ? instrumentSymbol(instrumentId) : ""}`}>
        <Sparkline points={prices ?? []} />
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card title="Place order (as Meridian Carbon Trading)">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Side</label>
              <select value={side} onChange={(e) => setSide(e.target.value)} className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm">
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Quantity</label>
              <input
                type="number"
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-28"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Limit price (€)</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="border border-slate-300 rounded-lg px-2 py-1.5 text-sm w-28"
              />
            </div>
            <Button onClick={placeOrder} disabled={busy || !instrumentId}>
              Submit
            </Button>
          </div>
        </Card>

        <Card title="My positions">
          <Table
            columns={[
              { key: "instrument", label: "Instrument" },
              { key: "quantity", label: "Quantity" },
              { key: "avg_cost_eur", label: "Avg cost (€)" },
            ]}
            rows={positions ?? []}
            renderCell={(row, key) => {
              if (key === "instrument") return instrumentSymbol(row.instrument_id);
              if (key === "quantity") return row.quantity.toLocaleString();
              if (key === "avg_cost_eur") return row.avg_cost_eur.toFixed(2);
              return row[key];
            }}
          />
        </Card>
      </div>

      <Card title="Open orders">
        <Table
          columns={[
            { key: "instrument", label: "Instrument" },
            { key: "side", label: "Side" },
            { key: "quantity", label: "Qty" },
            { key: "limit_price_eur", label: "Limit €" },
            { key: "status", label: "Status" },
            { key: "action", label: "" },
          ]}
          rows={orders ?? []}
          renderCell={(row, key) => {
            if (key === "instrument") return instrumentSymbol(row.instrument_id);
            if (key === "status") return <Badge status={row.status} />;
            if (key === "action")
              return (
                <Button variant="ghost" disabled={busy} onClick={() => cancel(row.id)}>
                  Cancel
                </Button>
              );
            return row[key];
          }}
        />
      </Card>

      <Card title="Recent trades">
        <Table
          columns={[
            { key: "instrument", label: "Instrument" },
            { key: "quantity", label: "Qty" },
            { key: "price_eur", label: "Price €" },
            { key: "executed_at", label: "Executed at" },
          ]}
          rows={trades ?? []}
          renderCell={(row, key) => {
            if (key === "instrument") return instrumentSymbol(row.instrument_id);
            if (key === "executed_at") return new Date(row.executed_at).toLocaleString();
            return row[key];
          }}
        />
      </Card>

      <Card title="What the real EUA market looks like — next to this demo order book">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 mb-4">
          The order book above is a simulated demo (a random-walk price series starting at €68/t) — not
          connected to any live feed. For scale: real-world EUA/carbon-derivatives trading is dominated by{" "}
          <a
            className="underline"
            href="https://ir.theice.com/press/news-details/2025/ICE-Announces-Record-Environmental-Market-Trading-in-2024/default.aspx"
            target="_blank"
            rel="noreferrer"
          >
            ICE Futures Europe
          </a>{" "}
          (read directly from ICE's own 24 Jan 2025 release): <strong>20.4 million environmental contracts
          traded in 2024 (+40% YoY), over $1 trillion in notional value for the fourth straight year</strong>.
          EEX (Leipzig) runs the EU's primary EUA auction instead of competing head-on in secondary trading.
        </div>
        <Table
          columns={[
            { key: "category", label: "Category" },
            { key: "metric_label", label: "Metric" },
            { key: "period", label: "Period" },
            { key: "value", label: "Value" },
            { key: "confidence", label: "" },
          ]}
          rows={marketReality ?? []}
          renderCell={(row, key) => {
            if (key === "category") return MARKET_REALITY_CATEGORY_LABELS[row.category] ?? row.category;
            if (key === "value") return formatRealityValue(row);
            if (key === "confidence") return <span className="text-xs text-slate-400 uppercase">{row.source_confidence}</span>;
            return row[key];
          }}
        />
        <details className="mt-3 text-xs text-slate-500">
          <summary className="cursor-pointer hover:text-slate-700">Per-row notes</summary>
          <ul className="mt-2 space-y-2">
            {(marketReality ?? [])
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
