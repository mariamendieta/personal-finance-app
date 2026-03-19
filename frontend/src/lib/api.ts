const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface AppConfig {
  family_name: string;
  is_demo: boolean;
  data_mode: string;
  brand: Record<string, string>;
  brand_palette: string[];
}

export interface CashFlowSummary {
  total_income: number;
  total_spending: number;
  net_income: number;
  months_available: string[];
}

export interface MonthlyExpense {
  month: string;
  display_category: string;
  amount: number;
  color: string;
  breakdown: { category: string; amount: number }[];
}

export interface MonthlyIncome {
  month: string;
  subcategory: string;
  amount: number;
}

export interface NetIncomeMonth {
  month: string;
  income: number;
  spending: number;
  net: number;
  cumulative: number;
}

export interface CategorySpending {
  category: string;
  total: number;
  percent: number;
}

export interface VendorSpending {
  vendor: string;
  total: number;
  percent: number;
}

export interface AssetAllocation {
  asset_class: string;
  value: number;
  percent: number;
}

export interface AccountHolding {
  account: string;
  account_type: string;
  value: number;
  cost: number;
  unrealized_gl: number;
  gl_pct: number;
  pct_of_portfolio: number;
}

export interface RetirementVsTaxableRow {
  asset_class: string;
  retirement: number;
  pct_retirement: number;
  taxable: number;
  pct_taxable: number;
  total: number;
  pct_portfolio: number;
}

export interface RetirementVsTaxable {
  rows: RetirementVsTaxableRow[];
  retirement_total: number;
  taxable_total: number;
  total: number;
}

export interface ComparisonAssetClass {
  asset_class: string;
  previous: number;
  current: number;
  change: number;
  change_pct: number;
}

export interface PortfolioComparison {
  current_snapshot: string;
  previous_snapshot: string;
  current_total: number;
  previous_total: number;
  change: number;
  pct_change: number;
  by_asset_class: ComparisonAssetClass[];
}

export interface ActionItem {
  task: string;
  assignee: string;
  category: string;
  date_created: string;
  status: string;
  date_completed: string;
}

async function postAPI<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function putAPI<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function deleteAPI<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// API functions
export const api = {
  getConfig: () => fetchAPI<AppConfig>("/api/config"),

  // Cash Flow
  getCashFlowSummary: (months = 12) => fetchAPI<CashFlowSummary>("/api/cashflow/summary", { months }),
  getMonthlyExpenses: (months = 12) => fetchAPI<MonthlyExpense[]>("/api/cashflow/monthly-expenses", { months }),
  getMonthlyIncome: (months = 12) => fetchAPI<MonthlyIncome[]>("/api/cashflow/monthly-income", { months }),
  getNetIncome: (months = 12) => fetchAPI<NetIncomeMonth[]>("/api/cashflow/net-income", { months }),
  getSpendingByCategory: (months = 12) => fetchAPI<CategorySpending[]>("/api/cashflow/spending-by-category", { months }),
  getTopVendors: (months = 12, limit = 10) => fetchAPI<VendorSpending[]>("/api/cashflow/top-vendors", { months, limit }),

  // Portfolio
  getSnapshots: () => fetchAPI<string[]>("/api/portfolio/snapshots"),
  getPortfolioSummary: (snapshot: string) => fetchAPI<{ total_value: number; snapshot: string }>("/api/portfolio/summary", { snapshot }),
  getAssetAllocation: (snapshot: string) => fetchAPI<AssetAllocation[]>("/api/portfolio/asset-allocation", { snapshot }),
  getByAccount: (snapshot: string) => fetchAPI<AccountHolding[]>("/api/portfolio/by-account", { snapshot }),
  getRetirementVsTaxable: (snapshot: string) => fetchAPI<RetirementVsTaxable>("/api/portfolio/retirement-vs-taxable", { snapshot }),
  getComparison: (current: string, previous: string) => fetchAPI<PortfolioComparison>("/api/portfolio/compare", { current, previous }),

  // Action Items
  getActionItems: () => fetchAPI<ActionItem[]>("/api/action-items/"),
  addActionItem: (task: string, assignee: string, category: string, date_created: string) =>
    postAPI<ActionItem[]>("/api/action-items/", { task, assignee, category, date_created }),
  updateActionItemStatus: (task: string, status: string, date_completed: string = "") =>
    putAPI<ActionItem[]>("/api/action-items/status", { task, status, date_completed }),
  deleteActionItem: (task: string) =>
    deleteAPI<ActionItem[]>("/api/action-items/", { task }),
};
