"use client";

import { useState, useMemo, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BudgetCategoryRow } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";
import MetricCard from "@/components/layout/MetricCard";

const PERIOD_OPTIONS = [
  { label: "This Month", months: 1 },
  { label: "Last 3 Months", months: 3 },
  { label: "Last 12 Months", months: 12 },
];

export default function BudgetPage() {
  const queryClient = useQueryClient();
  const [months, setMonths] = useState(1);

  // Editable budget state
  const [editedBudgets, setEditedBudgets] = useState<Record<string, number>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Add category form
  const [newCategory, setNewCategory] = useState("");
  const [newAmount, setNewAmount] = useState("");

  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });

  const { data: budgetData, isLoading } = useQuery({
    queryKey: ["budget-vs-actual", months],
    queryFn: () => api.getBudgetVsActual(months),
  });

  const { data: currentBudget } = useQuery({
    queryKey: ["budget"],
    queryFn: api.getBudget,
  });

  const { data: allCategories } = useQuery({
    queryKey: ["budget-categories"],
    queryFn: api.getBudgetCategories,
  });

  // Initialize editedBudgets from currentBudget
  useEffect(() => {
    if (currentBudget) {
      setEditedBudgets(currentBudget);
      setHasChanges(false);
    }
  }, [currentBudget]);

  const saveBudget = useMutation({
    mutationFn: (budgets: Record<string, number>) => api.saveBudget(budgets),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget"] });
      queryClient.invalidateQueries({ queryKey: ["budget-vs-actual"] });
      setHasChanges(false);
    },
  });

  const handleBudgetChange = (category: string, value: string) => {
    const num = parseFloat(value) || 0;
    setEditedBudgets((prev) => ({ ...prev, [category]: num }));
    setHasChanges(true);
  };

  const handleRemoveCategory = (category: string) => {
    const next = { ...editedBudgets };
    delete next[category];
    setEditedBudgets(next);
    setHasChanges(true);
  };

  const handleAddCategory = () => {
    if (!newCategory || !newAmount) return;
    const amount = parseFloat(newAmount);
    if (isNaN(amount) || amount <= 0) return;
    setEditedBudgets((prev) => ({ ...prev, [newCategory]: amount }));
    setHasChanges(true);
    setNewCategory("");
    setNewAmount("");
  };

  const handleSave = () => {
    saveBudget.mutate(editedBudgets);
  };

  // Categories available to add (not already in budget)
  const availableCategories = useMemo(() => {
    if (!allCategories) return [];
    const budgeted = new Set(Object.keys(editedBudgets));
    return allCategories.filter((c) => !budgeted.has(c)).sort();
  }, [allCategories, editedBudgets]);

  const familyName = config?.family_name || "Woffieta Family";
  const summary = budgetData?.summary;
  const categories = budgetData?.categories || [];

  return (
    <div>
      {/* Header */}
      <div
        className="pb-2 mb-6 border-b-[3px]"
        style={{
          borderImage:
            "linear-gradient(90deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1",
        }}
      >
        <h1 className="font-[Cormorant_Garamond,serif] text-[2.4rem] font-normal text-warm-charcoal leading-tight">
          {familyName}
        </h1>
        <p className="text-[0.85rem] font-light text-stone tracking-[0.1em] uppercase">
          Budget
        </p>
      </div>

      {/* Period Toggle */}
      <div className="flex items-center gap-2 mb-6">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.months}
            onClick={() => setMonths(opt.months)}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              months === opt.months
                ? "bg-azul text-white"
                : "bg-cool-white text-stone border border-cool-gray hover:text-azul"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-stone text-lg">Loading budget data...</p>
        </div>
      ) : (
        <>
          {/* Summary KPI Cards */}
          {summary && (
            <div className="grid grid-cols-4 gap-6 mb-8">
              <MetricCard
                label="Budget Used"
                value={formatPercent(summary.pct_used)}
                accent={summary.pct_used > 100 ? "coral" : "verde"}
              />
              <MetricCard
                label={summary.total_difference >= 0 ? "Under Budget" : "Over Budget"}
                value={formatCurrency(Math.abs(summary.total_difference))}
                accent={summary.total_difference >= 0 ? "verde" : "coral"}
              />
              <MetricCard
                label={`Total Budget (${months === 1 ? "Month" : `${months} Mo`})`}
                value={formatCurrency(summary.total_budget_for_period)}
                accent="azul"
              />
              <MetricCard
                label="Categories Status"
                value={`${summary.categories_over} over / ${summary.categories_under} under`}
                accent={summary.categories_over > 0 ? "coral" : "verde"}
              />
            </div>
          )}

          <hr className="border-cool-gray mb-8" />

          {/* Budget Table */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-[Lora,serif] text-lg text-warm-charcoal">
              Budget by Category
            </h2>
            {hasChanges && (
              <button
                onClick={handleSave}
                disabled={saveBudget.isPending}
                className="bg-azul text-white px-5 py-1.5 rounded font-semibold text-sm hover:bg-verde-claro disabled:opacity-40 transition-colors"
              >
                {saveBudget.isPending ? "Saving..." : "Save Changes"}
              </button>
            )}
          </div>

          <div className="overflow-x-auto rounded-lg border border-cool-gray">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-cool-white">
                  <th className="text-left px-4 py-3 font-semibold text-stone">
                    Category
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-stone w-36">
                    Monthly Budget
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-stone w-36">
                    Budget for Period
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-stone w-32">
                    Actual Spent
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-stone w-32">
                    Difference
                  </th>
                  <th className="text-left px-4 py-3 font-semibold text-stone w-40">
                    % Used
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-stone w-28">
                    12-Mo Avg
                  </th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {categories.map((row: BudgetCategoryRow) => {
                  const isOver = row.difference < 0;
                  const pctUsed = row.budget_for_period > 0 ? (row.actual_spent / row.budget_for_period) * 100 : 0;
                  const pctClamped = Math.min(pctUsed, 100);
                  const editedMonthly = editedBudgets[row.category];
                  const computedPeriodBudget =
                    editedMonthly !== undefined
                      ? editedMonthly * months
                      : row.budget_for_period;

                  return (
                    <tr
                      key={row.category}
                      className={`border-t border-cool-gray group ${
                        isOver ? "bg-coral/5" : "bg-verde-claro/5"
                      }`}
                    >
                      <td className="px-4 py-2.5 text-warm-charcoal font-medium">
                        {row.category}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <input
                          type="number"
                          min="0"
                          step="50"
                          value={editedMonthly ?? row.monthly_budget}
                          onChange={(e) =>
                            handleBudgetChange(row.category, e.target.value)
                          }
                          className="w-24 text-right text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul"
                        />
                      </td>
                      <td className="px-4 py-2.5 text-right text-stone">
                        {formatCurrency(computedPeriodBudget)}
                      </td>
                      <td className="px-4 py-2.5 text-right text-warm-charcoal">
                        {formatCurrency(row.actual_spent)}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-right font-medium ${
                          isOver ? "text-coral" : "text-verde-hoja"
                        }`}
                      >
                        {isOver ? "-" : "+"}
                        {formatCurrency(Math.abs(row.difference))}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-cool-gray rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isOver ? "bg-coral" : "bg-verde-claro"
                              }`}
                              style={{ width: `${pctClamped}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs font-medium w-12 text-right ${
                              isOver ? "text-coral" : "text-stone"
                            }`}
                          >
                            {formatPercent(pctUsed, 0)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-right text-stone">
                        {formatCurrency(row.avg_12mo)}
                      </td>
                      <td className="px-2 py-2.5">
                        <button
                          onClick={() => handleRemoveCategory(row.category)}
                          className="text-mid-gray hover:text-coral opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Remove from budget"
                        >
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M18 6L6 18M6 6l12 12" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  );
                })}

                {/* Add Category Row */}
                <tr className="border-t border-cool-gray bg-cool-white/50">
                  <td className="px-4 py-2.5">
                    <select
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      className="text-sm px-2 py-1 rounded border border-cool-gray w-full focus:outline-none focus:border-azul"
                    >
                      <option value="">Select category...</option>
                      {availableCategories.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <input
                      type="number"
                      min="0"
                      step="50"
                      placeholder="0"
                      value={newAmount}
                      onChange={(e) => setNewAmount(e.target.value)}
                      className="w-24 text-right text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul"
                      onKeyDown={(e) =>
                        e.key === "Enter" && handleAddCategory()
                      }
                    />
                  </td>
                  <td colSpan={5}></td>
                  <td className="px-2 py-2.5">
                    <button
                      onClick={handleAddCategory}
                      disabled={!newCategory || !newAmount}
                      className="text-azul hover:text-verde-claro disabled:opacity-30 transition-colors font-semibold text-sm"
                      title="Add category"
                    >
                      Add
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {categories.length === 0 && !isLoading && (
            <p className="text-stone text-center py-12">
              No budget categories set yet. Use the row above to add your first
              category.
            </p>
          )}
        </>
      )}
    </div>
  );
}
