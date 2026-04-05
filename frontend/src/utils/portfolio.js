/**
 * Portfolio persistence using localStorage.
 * A portfolio is a list of purchase entries.
 */

const KEY = "gold_portfolio";

export function loadPortfolio() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
}

export function savePortfolio(entries) {
  localStorage.setItem(KEY, JSON.stringify(entries));
}

export function addEntry(entry) {
  const portfolio = loadPortfolio();
  const newEntry = { ...entry, id: crypto.randomUUID(), createdAt: new Date().toISOString() };
  portfolio.push(newEntry);
  savePortfolio(portfolio);
  return newEntry;
}

export function removeEntry(id) {
  const portfolio = loadPortfolio().filter((e) => e.id !== id);
  savePortfolio(portfolio);
}
