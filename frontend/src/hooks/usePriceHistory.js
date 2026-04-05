import { useState, useEffect } from "react";
import { api } from "../utils/api";
import { subtractDays } from "../utils/constants";

export function usePriceHistory(days = 90) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    const start = subtractDays(days);
    const end = new Date().toISOString().split("T")[0];
    api.getPriceHistory(start, end)
      .then((res) => setData(res.prices || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [days]);

  return { data, loading, error };
}
