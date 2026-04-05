export const KARATS = [
  { key: "karat_22", label: "২২ ক্যারেট", labelEn: "22K" },
  { key: "karat_21", label: "২১ ক্যারেট", labelEn: "21K" },
  { key: "karat_18", label: "১৮ ক্যারেট", labelEn: "18K" },
  { key: "karat_24", label: "২৪ ক্যারেট (পাকা)", labelEn: "24K (Pure)" },
  { key: "sanatan",  label: "সনাতন",          labelEn: "Sanatan" },
];

export const UNITS = [
  { key: "bhari",  label: "ভরি",    labelEn: "Bhari" },
  { key: "ana",    label: "আনা",    labelEn: "Ana" },
  { key: "roti",   label: "রতি",    labelEn: "Roti" },
  { key: "gram",   label: "গ্রাম",  labelEn: "Gram" },
  { key: "tola",   label: "তোলা",   labelEn: "Tola" },
  { key: "ounce",  label: "আউন্স",  labelEn: "Ounce" },
];

export const RANGE_OPTIONS = [
  { label: "১ মাস", days: 30 },
  { label: "৩ মাস", days: 90 },
  { label: "৬ মাস", days: 180 },
  { label: "১ বছর", days: 365 },
  { label: "সব",    days: 9999 },
];

export function formatBDT(amount) {
  return new Intl.NumberFormat("bn-BD", {
    style: "currency",
    currency: "BDT",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(iso) {
  return new Intl.DateTimeFormat("bn-BD", {
    day: "numeric", month: "long", year: "numeric",
  }).format(new Date(iso));
}

export function subtractDays(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}
