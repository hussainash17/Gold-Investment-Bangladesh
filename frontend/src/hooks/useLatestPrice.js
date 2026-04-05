import { useState, useEffect } from "react";
import { api } from "../utils/api";

export function useLatestPrice() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getLatestPrice()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
