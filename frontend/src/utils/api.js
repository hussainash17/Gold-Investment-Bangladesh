const BASE_URL = import.meta.env.VITE_API_URL || "/api";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  getLatestPrice: () => get("/prices/latest"),
  getPriceHistory: (start, end) => get(`/prices?start=${start}&end=${end}`),
  getRoi: (params) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/prices/roi?${qs}`);
  },
};
