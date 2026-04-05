import { KARATS, formatBDT, formatDate } from "../utils/constants";

export default function PriceCard({ data }) {
  if (!data) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-16">
        <h2>আজকের সোনার দাম</h2>
        <span className="text-muted" style={{ fontSize: 13 }}>
          {formatDate(data.date)} | প্রতি ভরি
        </span>
      </div>

      <div className="grid-3" style={{ gap: 12 }}>
        {KARATS.map(({ key, label, labelEn }) => (
          <div key={key} style={{
            background: "var(--surface2)",
            borderRadius: 10,
            padding: "16px",
            borderLeft: "3px solid var(--gold)",
          }}>
            <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 6 }}>
              {label}
              <span style={{ marginLeft: 6, fontSize: 11, color: "#555" }}>({labelEn})</span>
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--gold)" }}>
              {data[key] ? formatBDT(data[key]) : "—"}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)", textAlign: "right" }}>
        উৎস: <a href="https://www.bajus.org/gold-price" target="_blank" rel="noreferrer">bajus.org</a>
      </div>
    </div>
  );
}
