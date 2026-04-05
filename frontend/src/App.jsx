import { useState } from "react";
import Header from "./components/Header";
import PriceCard from "./components/PriceCard";
import PriceChart from "./components/PriceChart";
import RoiCalculator from "./components/RoiCalculator";
import Portfolio from "./components/Portfolio";
import { useLatestPrice } from "./hooks/useLatestPrice";

const TABS = [
  { key: "dashboard", label: "ড্যাশবোর্ড" },
  { key: "calculator", label: "ROI ক্যালকুলেটর" },
  { key: "portfolio", label: "পোর্টফোলিও" },
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const { data, loading, error } = useLatestPrice();

  return (
    <>
      <Header />
      <main className="container" style={{ paddingBottom: 60 }}>
        <div className="tab-bar" style={{ marginBottom: 28 }}>
          {TABS.map(({ key, label }) => (
            <button key={key} className={`tab ${tab === key ? "active" : ""}`}
              onClick={() => setTab(key)}>
              {label}
            </button>
          ))}
        </div>

        {tab === "dashboard" && (
          <>
            {loading && <div className="loader" />}
            {error && (
              <div style={{ color: "var(--red)", textAlign: "center", padding: 32 }}>
                ডেটা লোড করতে সমস্যা হয়েছে: {error}
              </div>
            )}
            {data && <PriceCard data={data} />}
            <PriceChart />
          </>
        )}

        {tab === "calculator" && <RoiCalculator />}
        {tab === "portfolio" && <Portfolio />}
      </main>
    </>
  );
}
