"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, SubcategorySpending } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";
import MetricCard from "@/components/layout/MetricCard";
import Tabs from "@/components/layout/Tabs";
import ExpensesByCategory from "@/components/cashflow/ExpensesByCategory";
import IncomeBySource from "@/components/cashflow/IncomeBySource";
import NetIncomeChart from "@/components/cashflow/NetIncomeChart";
import SpendingTable from "@/components/cashflow/SpendingTable";
import TopVendorsChart from "@/components/cashflow/TopVendorsChart";
import AddCashFlowTab from "@/components/cashflow/AddCashFlowTab";

const ytdMonths = new Date().getMonth() || 1; // Completed months this year (Mar=2: Jan+Feb, Jan defaults to 1)

const PERIOD_OPTIONS = [
  { label: "YTD", value: ytdMonths, key: "ytd" },
  { label: "Last month", value: 1, key: "1m" },
  { label: "Last 3 months", value: 3, key: "3m" },
  { label: "Last 6 months", value: 6, key: "6m" },
  { label: "Last 12 months", value: 12, key: "12m" },
];

export default function CashFlowPage() {
  const [detailMonths, setDetailMonths] = useState(12);
  const [selectedPeriodKey, setSelectedPeriodKey] = useState("12m");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubcategory, setSelectedSubcategory] = useState<string | null>(null);
  const [hiddenOutflows, setHiddenOutflows] = useState<Set<string>>(new Set());
  const [hiddenInflows, setHiddenInflows] = useState<Set<string>>(new Set());

  const toggleOutflow = (cat: string) => {
    setHiddenOutflows(prev => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };
  const toggleInflow = (sub: string) => {
    setHiddenInflows(prev => {
      const next = new Set(prev);
      next.has(sub) ? next.delete(sub) : next.add(sub);
      return next;
    });
  };
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["cashflow-summary"],
    queryFn: () => api.getCashFlowSummary(12),
  });
  const { data: expenses } = useQuery({
    queryKey: ["monthly-expenses"],
    queryFn: () => api.getMonthlyExpenses(12),
  });
  const { data: income } = useQuery({
    queryKey: ["monthly-income"],
    queryFn: () => api.getMonthlyIncome(12),
  });
  const { data: netIncome } = useQuery({
    queryKey: ["net-income"],
    queryFn: () => api.getNetIncome(12),
  });
  const { data: categories } = useQuery({
    queryKey: ["spending-by-category", detailMonths],
    queryFn: () => api.getSpendingByCategory(detailMonths),
  });
  const { data: vendors } = useQuery({
    queryKey: ["top-vendors", detailMonths],
    queryFn: () => api.getTopVendors(detailMonths),
  });
  const { data: subcategories } = useQuery({
    queryKey: ["subcategories", selectedCategory, detailMonths],
    queryFn: () => api.getSubcategories(selectedCategory!, detailMonths),
    enabled: !!selectedCategory,
  });
  const { data: subcatVendors } = useQuery({
    queryKey: ["subcat-vendors", selectedCategory, selectedSubcategory, detailMonths],
    queryFn: () => api.getSubcategoryVendors(selectedCategory!, selectedSubcategory!, detailMonths),
    enabled: !!selectedCategory && !!selectedSubcategory,
  });

  const familyName = config?.family_name || "Woffieta Family";

  // Compute filtered totals from monthly data based on hidden filters
  const filteredTotalOutflows = expenses
    ? expenses.filter(e => !hiddenOutflows.has(e.display_category)).reduce((s, e) => s + e.amount, 0)
    : summary?.total_spending || 0;
  const filteredTotalInflows = income
    ? income.filter(i => !hiddenInflows.has(i.subcategory)).reduce((s, i) => s + i.amount, 0)
    : summary?.total_income || 0;
  const filteredNetCashFlow = filteredTotalInflows - filteredTotalOutflows;
  const hasFilters = hiddenOutflows.size > 0 || hiddenInflows.size > 0;
  const filterSuffix = hasFilters ? " (filtered)" : "";

  return (
    <div>
      {/* Header */}
      <div className="pb-2 mb-6 border-b-[3px]"
        style={{ borderImage: "linear-gradient(90deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1" }}>
        <h1 className="font-[Cormorant_Garamond,serif] text-[2.4rem] font-normal text-warm-charcoal leading-tight">
          {familyName}
        </h1>
        <p className="text-[0.85rem] font-light text-stone tracking-[0.1em] uppercase">
          Cash Flow
        </p>
      </div>

      <Tabs tabs={["Dashboard", "Add Data"]}>
        {/* Dashboard tab */}
        <div>
          {loadingSummary ? (
            <div className="flex items-center justify-center h-64">
              <p className="text-stone text-lg">Loading cash flow data...</p>
            </div>
          ) : (
            <>
              {summary && (
                <div className="grid grid-cols-3 gap-6 mb-8">
                  <MetricCard label={`Total Inflows (12 mo)${filterSuffix}`} value={formatCurrency(filteredTotalInflows)} accent="azul" />
                  <MetricCard label={`Total Outflows (12 mo)${filterSuffix}`} value={formatCurrency(filteredTotalOutflows)} accent="coral" />
                  <MetricCard label={`Net Cash Flow (12 mo)${filterSuffix}`} value={formatCurrency(filteredNetCashFlow)} accent="verde" />
                </div>
              )}

              <hr className="border-cool-gray mb-8" />

              {expenses && (
                <ExpensesByCategory
                  data={expenses}
                  hiddenCategories={hiddenOutflows}
                  onToggleCategory={toggleOutflow}
                />
              )}
              <div className="mt-10" />
              {income && (
                <IncomeBySource
                  data={income}
                  hiddenSubcategories={hiddenInflows}
                  onToggleSubcategory={toggleInflow}
                />
              )}
              <div className="mt-10" />
              {netIncome && <NetIncomeChart data={netIncome} incomeData={income} expenseData={expenses} />}

              <hr className="border-cool-gray my-8" />

              <div className="flex items-center gap-3 mb-6">
                <label className="text-sm font-medium text-stone">Time Period:</label>
                <div className="flex gap-1 bg-cool-white rounded-lg p-1 border border-cool-gray">
                  {PERIOD_OPTIONS.map(opt => (
                    <button
                      key={opt.key}
                      onClick={() => { setDetailMonths(opt.value); setSelectedPeriodKey(opt.key); }}
                      className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                        selectedPeriodKey === opt.key
                          ? "bg-azul text-white font-medium"
                          : "text-stone hover:text-warm-charcoal hover:bg-cool-gray"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <div>{categories && <SpendingTable data={categories} periodLabel={PERIOD_OPTIONS.find(o => o.value === detailMonths)?.label || ""} selectedCategory={selectedCategory} onCategoryClick={(cat) => { setSelectedCategory(cat === selectedCategory ? null : cat); setSelectedSubcategory(null); }} />}</div>
                <div>
                  {selectedCategory && subcategories ? (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal">
                          {selectedCategory}
                        </h2>
                        <button onClick={() => setSelectedCategory(null)} className="text-sm text-stone hover:text-coral">
                          Clear
                        </button>
                      </div>
                      <div className="overflow-x-auto rounded-lg border border-cool-gray">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-cool-white">
                              <th className="text-left px-4 py-3 font-semibold text-stone">Subcategory</th>
                              <th className="text-right px-4 py-3 font-semibold text-stone">Total</th>
                              <th className="text-right px-4 py-3 font-semibold text-stone">%</th>
                            </tr>
                          </thead>
                          <tbody>
                            {subcategories.map(row => (
                              <tr
                                key={row.subcategory}
                                onClick={() => setSelectedSubcategory(row.subcategory === selectedSubcategory ? null : row.subcategory)}
                                className={`border-t border-cool-gray cursor-pointer transition-colors ${
                                  selectedSubcategory === row.subcategory
                                    ? "bg-verde-hoja/10 border-l-2 border-l-verde-hoja"
                                    : "hover:bg-cool-white/50"
                                }`}
                              >
                                <td className="px-4 py-2.5">{row.subcategory}</td>
                                <td className="px-4 py-2.5 text-right font-medium">{formatCurrency(row.total, 2)}</td>
                                <td className="px-4 py-2.5 text-right text-stone">{formatPercent(row.percent)}</td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot>
                            <tr className="border-t-2 border-warm-charcoal bg-cool-white font-semibold">
                              <td className="px-4 py-2.5">Total</td>
                              <td className="px-4 py-2.5 text-right">{formatCurrency(subcategories.reduce((s, r) => s + r.total, 0), 2)}</td>
                              <td className="px-4 py-2.5 text-right">100%</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-stone text-sm">
                      Click a category to see subcategory breakdown
                    </div>
                  )}
                </div>
              </div>

              {selectedSubcategory && subcatVendors && (
                <div className="mt-8">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="font-[Lora,serif] text-xl text-warm-charcoal">
                      {selectedCategory} &rsaquo; {selectedSubcategory} &mdash; Vendors
                    </h2>
                    <button onClick={() => setSelectedSubcategory(null)} className="text-sm text-stone hover:text-coral">
                      Clear
                    </button>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-cool-gray max-w-2xl">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-cool-white">
                          <th className="text-left px-4 py-3 font-semibold text-stone">Vendor</th>
                          <th className="text-right px-4 py-3 font-semibold text-stone">Total</th>
                          <th className="text-right px-4 py-3 font-semibold text-stone">Transactions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {subcatVendors.map(row => (
                          <tr key={row.vendor} className="border-t border-cool-gray hover:bg-cool-white/50">
                            <td className="px-4 py-2.5">{row.vendor}</td>
                            <td className="px-4 py-2.5 text-right font-medium">{formatCurrency(row.total, 2)}</td>
                            <td className="px-4 py-2.5 text-right text-stone">{row.count}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="border-t-2 border-warm-charcoal bg-cool-white font-semibold">
                          <td className="px-4 py-2.5">Total</td>
                          <td className="px-4 py-2.5 text-right">{formatCurrency(subcatVendors.reduce((s, r) => s + r.total, 0), 2)}</td>
                          <td className="px-4 py-2.5 text-right">{subcatVendors.reduce((s, r) => s + r.count, 0)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}

              <div className="mt-10">
                {vendors && <TopVendorsChart data={vendors} periodLabel={PERIOD_OPTIONS.find(o => o.value === detailMonths)?.label || ""} />}
              </div>
            </>
          )}
        </div>

        {/* Add Data tab */}
        <AddCashFlowTab />
      </Tabs>
    </div>
  );
}
