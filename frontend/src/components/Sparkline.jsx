export default function Sparkline({ points, width = 600, height = 120, stroke = "#0f172a" }) {
  if (!points || points.length < 2) return <div className="text-sm text-slate-400">Not enough data</div>;

  const values = points.map((p) => p.price_eur);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * width;
    const y = height - ((p.price_eur - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-28">
        <polyline points={coords.join(" ")} fill="none" stroke={stroke} strokeWidth="2" />
      </svg>
      <div className="flex justify-between text-xs text-slate-400 mt-1">
        <span>€{min.toFixed(2)}</span>
        <span>{points[0].price_date} → {points[points.length - 1].price_date}</span>
        <span>€{max.toFixed(2)}</span>
      </div>
    </div>
  );
}
