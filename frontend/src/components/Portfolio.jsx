import { useState, useEffect } from "react";
import { api } from "../utils/api";
import { KARATS, UNITS, formatBDT } from "../utils/constants";
import { loadPortfolio, addEntry, removeEntry } from "../utils/portfolio";

const DEFAULT_FORM = { buy_date: "", amount: "", unit: "bhari", karat: "karat_22", note: "" };

export default function Portfolio() {
  const [entries, setEntries] = useState([]);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [results, setResults] = useState({});
  const [adding, setAdding] = useState(false);
  const [latestPrice, setLatestPrice] = useState(null);

  useEffect(() => {
    setEntries(loadPortfolio());
    api.getLatestPrice().then(setLatestPrice).catch(() => {});
  }, []);

  useEffect(() => {
    entries.forEach((entry) => {
      if (results[entry.id]) return;
      api.getRoi({
        buy_date: entry.buy_date,
        amount: entry.amount,
        unit: entry.unit,
        karat: entry.karat,
      }).then((res) => setResults((prev) => ({ ...prev, [entry.id]: res })))
        .catch(() => {});
    });
  }, [entries]);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleAdd = (e) => {
    e.preventDefault();
    const entry = addEntry(form);
    setEntries(loadPortfolio());
    setForm(DEFAULT_FORM);
    setAdding(false);
  };

  const handleRemove = (id) => {
    removeEntry(id);
    setEntries(loadPortfolio());
    setResults((prev) => { const r = { ...prev }; delete r[id]; return r; });
  };

  const totalBuyValue = Object.values(results).reduce((s, r) => s + (r?.buy_value_bdt || 0), 0);
  const totalCurrentValue = Object.values(results).reduce((s, r) => s + (r?.current_value_bdt || 0), 0);
  const totalPL = totalCurrentValue - totalBuyValue;

  return (
    <div className="card mt-24">
      <div className="flex items-center justify-between mb-16">
        <h2>আমার পোর্টফোলিও</h2>
        <button className="primary" style={{ padding: "8px 16px", fontSize: 14 }}
          onClick={() => setAdding(!adding)}>
          {adding ? "বাতিল" : "+ নতুন যোগ করুন"}
        </button>
      </div>

      {adding && (
        <form onSubmit={handleAdd} style={{
          background: "var(--surface2)", borderRadius: 10, padding: 20, marginBottom: 20,
        }}>
          <div className="grid-2" style={{ gap: 12 }}>
            <div>
              <label>ক্রয়ের তারিখ</label>
              <input type="date" max={new Date().toISOString().split("T")[0]}
                value={form.buy_date} onChange={update("buy_date")} required />
            </div>
            <div>
              <label>পরিমাণ</label>
              <input type="number" min="0.01" step="0.01" placeholder="২.৫"
                value={form.amount} onChange={update("amount")} required />
            </div>
            <div>
              <label>একক</label>
              <select value={form.unit} onChange={update("unit")}>
                {UNITS.map(({ key, label }) => <option key={key} value={key}>{label}</option>)}
              </select>
            </div>
            <div>
              <label>ক্যারেট</label>
              <select value={form.karat} onChange={update("karat")}>
                {KARATS.map(({ key, label }) => <option key={key} value={key}>{label}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <label>নোট (ঐচ্ছিক)</label>
            <input type="text" placeholder="যেমন: বিবাহবার্ষিকী উপহার"
              value={form.note} onChange={update("note")} />
          </div>
          <button type="submit" className="primary" style={{ marginTop: 16, width: "100%" }}>
            পোর্টফোলিওতে যোগ করুন
          </button>
        </form>
      )}

      {entries.length === 0 ? (
        <p className="text-muted" style={{ fontSize: 14, textAlign: "center", padding: "32px 0" }}>
          এখনো কোনো সোনা যোগ করা হয়নি।
        </p>
      ) : (
        <>
          {/* Summary */}
          {totalBuyValue > 0 && (
            <div className="grid-3" style={{ gap: 12, marginBottom: 20 }}>
              <SummaryCard label="মোট ক্রয়মূল্য" value={formatBDT(totalBuyValue)} />
              <SummaryCard label="বর্তমান মূল্য" value={formatBDT(totalCurrentValue)} />
              <SummaryCard
                label="মোট লাভ/ক্ষতি"
                value={`${totalPL >= 0 ? "+" : ""}${formatBDT(Math.abs(totalPL))}`}
                color={totalPL >= 0 ? "var(--green)" : "var(--red)"}
              />
            </div>
          )}

          {/* Entries */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {entries.map((entry) => (
              <PortfolioEntry
                key={entry.id}
                entry={entry}
                roi={results[entry.id]}
                onRemove={() => handleRemove(entry.id)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }) {
  return (
    <div style={{ background: "var(--surface2)", borderRadius: 10, padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || "var(--text)" }}>{value}</div>
    </div>
  );
}

function PortfolioEntry({ entry, roi, onRemove }) {
  const karat = KARATS.find((k) => k.key === entry.karat);
  const unit = UNITS.find((u) => u.key === entry.unit);
  const isProfit = roi?.is_profit;

  return (
    <div style={{
      background: "var(--surface2)", borderRadius: 10, padding: 16,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      gap: 12, flexWrap: "wrap",
    }}>
      <div>
        <div style={{ fontWeight: 600 }}>
          {entry.amount} {unit?.label} — {karat?.label}
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
          {entry.buy_date}{entry.note ? ` · ${entry.note}` : ""}
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        {roi ? (
          <>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 16, fontWeight: 600 }}>{formatBDT(roi.current_value_bdt)}</div>
              <div style={{ fontSize: 13, color: isProfit ? "var(--green)" : "var(--red)" }}>
                {isProfit ? "+" : ""}{roi.percent_change}%
              </div>
            </div>
          </>
        ) : (
          <div style={{ width: 20, height: 20, border: "2px solid var(--gold)", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
        )}
        <button
          onClick={onRemove}
          style={{ background: "rgba(239,68,68,0.1)", color: "var(--red)", padding: "6px 12px", fontSize: 13, borderRadius: 6 }}
        >
          মুছুন
        </button>
      </div>
    </div>
  );
}
