import { useState } from "react";
import { api } from "../utils/api";
import { KARATS, UNITS, formatBDT } from "../utils/constants";

const DEFAULT_FORM = {
  buy_date: "",
  amount: "",
  unit: "bhari",
  karat: "karat_22",
};

export default function RoiCalculator() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const calculate = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.getRoi(form);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="card mt-24">
      <h2 className="mb-16">ROI ক্যালকুলেটর</h2>
      <p className="text-muted" style={{ fontSize: 14, marginBottom: 20 }}>
        আপনি কবে কত সোনা কিনেছিলেন? এখন তার মূল্য কত?
      </p>

      <form onSubmit={calculate}>
        <div className="grid-2" style={{ gap: 16 }}>
          <div>
            <label>ক্রয়ের তারিখ</label>
            <input
              type="date"
              max={today}
              value={form.buy_date}
              onChange={update("buy_date")}
              required
            />
          </div>
          <div>
            <label>পরিমাণ</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              placeholder="যেমন: 2.5"
              value={form.amount}
              onChange={update("amount")}
              required
            />
          </div>
          <div>
            <label>একক</label>
            <select value={form.unit} onChange={update("unit")}>
              {UNITS.map(({ key, label, labelEn }) => (
                <option key={key} value={key}>{label} ({labelEn})</option>
              ))}
            </select>
          </div>
          <div>
            <label>ক্যারেট</label>
            <select value={form.karat} onChange={update("karat")}>
              {KARATS.map(({ key, label, labelEn }) => (
                <option key={key} value={key}>{label} ({labelEn})</option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          className="primary"
          style={{ marginTop: 20, width: "100%" }}
          disabled={loading}
        >
          {loading ? "হিসাব করা হচ্ছে..." : "রিটার্ন হিসাব করুন"}
        </button>
      </form>

      {error && (
        <div style={{
          marginTop: 16,
          padding: 14,
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: 8,
          color: "var(--red)",
          fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {result && <RoiResult result={result} />}
    </div>
  );
}

function RoiResult({ result }) {
  const isProfit = result.is_profit;
  const sign = isProfit ? "+" : "";
  const pctColor = isProfit ? "var(--green)" : "var(--red)";

  return (
    <div style={{
      marginTop: 24,
      padding: 20,
      background: "var(--surface2)",
      borderRadius: 10,
      border: `1px solid ${isProfit ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
    }}>
      <div className="flex items-center justify-between mb-16">
        <h3>ফলাফল</h3>
        <span className={`badge ${isProfit ? "profit" : "loss"}`}>
          {sign}{result.percent_change}%
        </span>
      </div>

      <div className="grid-2" style={{ gap: 12 }}>
        <StatRow label="ক্রয়মূল্য" value={formatBDT(result.buy_value_bdt)} />
        <StatRow label="বর্তমান মূল্য" value={formatBDT(result.current_value_bdt)} />
        <StatRow
          label="লাভ / ক্ষতি"
          value={`${sign}${formatBDT(Math.abs(result.profit_loss_bdt))}`}
          valueColor={pctColor}
        />
        <StatRow label="রিটার্ন" value={`${sign}${result.percent_change}%`} valueColor={pctColor} />
        <StatRow label="ক্রয়ের তারিখ" value={result.buy_date} />
        <StatRow label="আজকের তারিখ" value={result.current_date} />
      </div>
    </div>
  );
}

function StatRow({ label, value, valueColor }) {
  return (
    <div style={{ padding: "12px", background: "var(--surface)", borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 17, fontWeight: 600, color: valueColor || "var(--text)" }}>{value}</div>
    </div>
  );
}
