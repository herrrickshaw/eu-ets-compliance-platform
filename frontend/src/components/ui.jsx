export function Card({ title, children, className = "" }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-200 p-5 ${className}`}>
      {title && <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">{title}</h3>}
      {children}
    </div>
  );
}

export function Stat({ label, value, sub, tone = "slate" }) {
  const tones = {
    slate: "text-slate-900",
    green: "text-emerald-600",
    red: "text-rose-600",
    amber: "text-amber-600",
  };
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-bold ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

export function Badge({ status }) {
  const map = {
    compliant: "bg-emerald-100 text-emerald-700",
    open: "bg-slate-100 text-slate-600",
    short: "bg-amber-100 text-amber-700",
    penalized: "bg-rose-100 text-rose-700",
    verified: "bg-emerald-100 text-emerald-700",
    pending: "bg-amber-100 text-amber-700",
    non_conformance: "bg-rose-100 text-rose-700",
    approved: "bg-emerald-100 text-emerald-700",
    draft: "bg-slate-100 text-slate-600",
    submitted: "bg-blue-100 text-blue-700",
    doc_issued: "bg-emerald-100 text-emerald-700",
    reconciled: "bg-emerald-100 text-emerald-700",
    held: "bg-blue-100 text-blue-700",
    issued: "bg-emerald-100 text-emerald-700",
    staged: "bg-amber-100 text-amber-700",
    retired: "bg-slate-200 text-slate-600",
    filled: "bg-emerald-100 text-emerald-700",
    cancelled: "bg-slate-100 text-slate-400",
    authorised: "bg-emerald-100 text-emerald-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status] || "bg-slate-100 text-slate-600"}`}>
      {status?.replace(/_/g, " ")}
    </span>
  );
}

export function Table({ columns, rows, renderCell }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-slate-500 uppercase border-b border-slate-200">
            {columns.map((c) => (
              <th key={c.key} className="py-2 pr-4 font-medium">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id ?? i} className="border-b border-slate-100 hover:bg-slate-50">
              {columns.map((c) => (
                <td key={c.key} className="py-2 pr-4 text-slate-700">
                  {renderCell ? renderCell(row, c.key) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="py-6 text-center text-slate-400">
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Button({ children, onClick, variant = "primary", disabled }) {
  const variants = {
    primary: "bg-slate-900 text-white hover:bg-slate-700",
    ghost: "bg-slate-100 text-slate-700 hover:bg-slate-200",
    danger: "bg-rose-600 text-white hover:bg-rose-500",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed ${variants[variant]}`}
    >
      {children}
    </button>
  );
}
