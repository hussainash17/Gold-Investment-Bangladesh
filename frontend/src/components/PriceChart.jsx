import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { usePriceHistory } from "../hooks/usePriceHistory";
import { RANGE_OPTIONS, KARATS, formatBDT } from "../utils/constants";

const COLORS = ["#C8A951", "#E8B560", "#A07830", "#F5E6A3", "#8B6914"];

export default function PriceChart() {
  const [days, setDays] = useState(90);
  const [selectedKarats, setSelectedKarats] = useState(["karat_22"]);
  const { data, loading } = usePriceHistory(days);

  const toggleKarat = (key) => {
    setSelectedKarats((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const chartData = data.map((record) => ({
    date: record.date,
    ...Object.fromEntries(
      KARATS.map(({ key }) => [key, record[key] ? Number(record[key]) : null])
    ),
  }));

  return (
    <div className="card mt-24">
      <div className="flex items-center justify-between flex-wrap" style={{ gap: 12, marginBottom: 20 }}>
        <h2>মূল্যের ইতিহাস</h2>
        <div style={{ display: "flex", gap: 6 }}>
          {RANGE_OPTIONS.map(({ label, days: d }) => (
            <button
              key={d}
              className={days === d ? "primary" : "ghost"}
              style={{ padding: "6px 12px", fontSize: 13 }}
              onClick={() => setDays(d)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {KARATS.map(({ key, label }) => (
          <button
            key={key}
            className={selectedKarats.includes(key) ? "primary" : "ghost"}
            style={{ padding: "4px 10px", fontSize: 13 }}
            onClick={() => toggleKarat(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader" />
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2A2A" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#888", fontSize: 12 }}
              tickFormatter={(d) => d.slice(5)}
            />
            <YAxis
              tick={{ fill: "#888", fontSize: 12 }}
              tickFormatter={(v) => `৳${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{ background: "#1A1A1A", border: "1px solid #3A3A3A", borderRadius: 8 }}
              labelStyle={{ color: "#888" }}
              formatter={(value, name) => [
                formatBDT(value),
                KARATS.find((k) => k.key === name)?.label || name,
              ]}
            />
            {selectedKarats.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
