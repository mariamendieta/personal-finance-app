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

export interface SubcategorySpending {
  subcategory: string;
  total: number;
  percent: number;
}

export interface SubcategoryVendor {
  vendor: string;
  total: number;
  count: number;
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

export interface Account {
  label: string;
  filePrefix: string;
  hidden: boolean;
}

export interface AccountsList {
  credit_cards: Account[];
  bank_accounts: Account[];
}

export interface ActionItem {
  task: string;
  assignee: string;
  category: string;
  date_created: string;
  status: string;
  date_completed: string;
}

export interface BudgetCategoryRow {
  category: string;
  monthly_budget: number;
  budget_for_period: number;
  actual_spent: number;
  difference: number;
  avg_12mo: number;
}

export interface BudgetSummary {
  total_budget_for_period: number;
  total_actual: number;
  total_difference: number;
  pct_used: number;
  categories_over: number;
  categories_under: number;
}

export interface BudgetVsActual {
  categories: BudgetCategoryRow[];
  summary: BudgetSummary;
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
  getSubcategories: (category: string, months = 12) => fetchAPI<SubcategorySpending[]>("/api/cashflow/subcategories", { category, months }),
  getSubcategoryVendors: (category: string, subcategory: string, months = 12) => fetchAPI<SubcategoryVendor[]>("/api/cashflow/subcategory-vendors", { category, subcategory, months }),
  getTopVendors: (months = 12, limit = 10) => fetchAPI<VendorSpending[]>("/api/cashflow/top-vendors", { months, limit }),

  // Portfolio
  getSnapshots: () => fetchAPI<string[]>("/api/portfolio/snapshots"),
  getPortfolioSummary: (snapshot: string) => fetchAPI<{ total_value: number; snapshot: string }>("/api/portfolio/summary", { snapshot }),
  getAssetAllocation: (snapshot: string) => fetchAPI<AssetAllocation[]>("/api/portfolio/asset-allocation", { snapshot }),
  getByAccount: (snapshot: string) => fetchAPI<AccountHolding[]>("/api/portfolio/by-account", { snapshot }),
  getRetirementVsTaxable: (snapshot: string) => fetchAPI<RetirementVsTaxable>("/api/portfolio/retirement-vs-taxable", { snapshot }),
  getComparison: (current: string, previous: string) => fetchAPI<PortfolioComparison>("/api/portfolio/compare", { current, previous }),

  // Budget
  getBudget: () => fetchAPI<Record<string, number>>("/api/budget/"),
  saveBudget: (budgets: Record<string, number>) =>
    putAPI<Record<string, number>>("/api/budget/", { budgets }),
  getBudgetVsActual: (months = 1) => fetchAPI<BudgetVsActual>("/api/budget/vs-actual", { months }),
  getBudgetCategories: () => fetchAPI<string[]>("/api/budget/categories"),

  // Balances
  getBalances: (date: string) => fetchAPI<Record<string, number>>("/api/balances/", { date }),
  saveBalances: (date: string, balances: Record<string, number>) =>
    putAPI<Record<string, number>>("/api/balances/", { date, balances }),

  // Accounts
  getAccounts: () => fetchAPI<AccountsList>("/api/accounts/"),
  addAccount: (account_type: string, label: string, file_prefix: string) =>
    postAPI<AccountsList>("/api/accounts/", { account_type, label, file_prefix }),
  toggleAccount: (account_type: string, file_prefix: string, hidden: boolean) =>
    putAPI<AccountsList>("/api/accounts/toggle", { account_type, file_prefix, hidden }),

  // Action Items
  getActionItems: () => fetchAPI<ActionItem[]>("/api/action-items/"),
  addActionItem: (task: string, assignee: string, category: string, date_created: string) =>
    postAPI<ActionItem[]>("/api/action-items/", { task, assignee, category, date_created }),
  updateActionItemStatus: (task: string, status: string, date_completed: string = "") =>
    putAPI<ActionItem[]>("/api/action-items/status", { task, status, date_completed }),
  editActionItem: (old_task: string, task: string, assignee: string, category: string) =>
    putAPI<ActionItem[]>("/api/action-items/edit", { old_task, task, assignee, category }),
  deleteActionItem: (task: string) =>
    deleteAPI<ActionItem[]>("/api/action-items/", { task }),
};
