"use client";

import { useState, useMemo } from "react";
import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import type { NetIncomeMonth, MonthlyIncome, MonthlyExpense } from "@/lib/api";
import { formatCurrency, formatMonth } from "@/lib/format";

export default function NetIncomeChart({
  data,
  incomeData,
  expenseData,
}: {
  data: NetIncomeMonth[];
  incomeData?: MonthlyIncome[];
  expenseData?: MonthlyExpense[];
}) {
  // Derive unique income subcategories
  const incomeSubcategories = useMemo(() => {
    if (!incomeData) return [];
    return [...new Set(incomeData.map(d => d.subcategory))].sort();
  }, [incomeData]);

  // Derive unique display categories (main categories used in bar chart)
  const spendingCategories = useMemo(() => {
    if (!expenseData) return [];
    return [...new Set(expenseData.map(d => d.display_category))].sort();
  }, [expenseData]);

  const [excludedInflows, setExcludedInflows] = useState<Set<string>>(new Set());
  const [excludedOutflows, setExcludedOutflows] = useState<Set<string>>(new Set());

  const toggleInflow = (subcat: string) => {
    setExcludedInflows(prev => {
      const next = new Set(prev);
      next.has(subcat) ? next.delete(subcat) : next.add(subcat);
      return next;
    });
  };

  const toggleOutflow = (cat: string) => {
    setExcludedOutflows(prev => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  const hasExclusions = excludedInflows.size > 0 || excludedOutflows.size > 0;

  // Compute adjusted data
  const chartData = useMemo(() => {
    if (!hasExclusions || (!incomeData && !expenseData)) {
      return data.map(d => ({ ...d, monthLabel: formatMonth(d.month) }));
    }

    // Sum excluded income per month
    const excludedIncomeByMonth: Record<string, number> = {};
    if (incomeData && excludedInflows.size > 0) {
      for (const item of incomeData) {
        if (excludedInflows.has(item.subcategory)) {
          excludedIncomeByMonth[item.month] = (excludedIncomeByMonth[item.month] || 0) + item.amount;
        }
      }
    }

    // Sum excluded spending per month (using display categories)
    const excludedSpendingByMonth: Record<string, number> = {};
    if (expenseData && excludedOutflows.size > 0) {
      for (const item of expenseData) {
        if (excludedOutflows.has(item.display_category)) {
          excludedSpendingByMonth[item.month] = (excludedSpendingByMonth[item.month] || 0) + item.amount;
        }
      }
    }

    let cumulative = 0;
    return data.map(d => {
      const adjIncome = d.income - (excludedIncomeByMonth[d.month] || 0);
      const adjSpending = d.spending - (excludedSpendingByMonth[d.month] || 0);
      const adjNet = adjIncome - adjSpending;
      cumulative += adjNet;
      return {
        ...d,
        income: adjIncome,
        spending: adjSpending,
        net: adjNet,
        cumulative,
        monthLabel: formatMonth(d.month),
      };
    });
  }, [data, incomeData, expenseData, excludedInflows, excludedOutflows, hasExclusions]);

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Net Cash Flow per Month &amp; Cumulative
      </h2>

      {(incomeSubcategories.length > 0 || spendingCategories.length > 0) && (
        <div className="space-y-2 mb-4">
          {incomeSubcategories.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-stone w-28">Exclude inflows:</span>
              {incomeSubcategories.map(subcat => (
                <button
                  key={subcat}
                  onClick={() => toggleInflow(subcat)}
                  className={`px-2.5 py-0.5 text-xs rounded-full border transition-colors ${
                    excludedInflows.has(subcat)
                      ? "bg-coral/15 text-coral border-coral line-through font-medium"
                      : "border-cool-gray text-stone bg-cool-white hover:border-stone"
                  }`}
                >
                  {subcat}
                </button>
              ))}
            </div>
          )}
          {spendingCategories.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-stone w-28">Exclude outflows:</span>
              {spendingCategories.map(cat => (
                <button
                  key={cat}
                  onClick={() => toggleOutflow(cat)}
                  className={`px-2.5 py-0.5 text-xs rounded-full border transition-colors ${
                    excludedOutflows.has(cat)
                      ? "bg-coral/15 text-coral border-coral line-through font-medium"
                      : "border-cool-gray text-stone bg-cool-white hover:border-stone"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
          {hasExclusions && (
            <button onClick={() => { setExcludedInflows(new Set()); setExcludedOutflows(new Set()); }}
              className="text-xs text-stone hover:text-azul">
              Reset all filters
            </button>
          )}
        </div>
      )}

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 60, bottom: 5, left: 20 }}>
          <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="left"
            tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            label={{ value: "Monthly Cash Flow ($)", angle: -90, position: "insideLeft", offset: -5, style: { fontSize: 12 } }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            label={{ value: "Cumulative ($)", angle: 90, position: "insideRight", offset: -5, style: { fontSize: 12 } }}
          />
          <Tooltip
            formatter={(value: number, name: string) => [formatCurrency(value), name]}
            labelFormatter={(label: string) => label}
          />
          <Legend wrapperStyle={{ paddingTop: 8 }} />
          <Bar yAxisId="left" dataKey="net" name="Monthly Net" barSize={30}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.net >= 0 ? "#1B4965" : "#E07A5F"} />
            ))}
          </Bar>
          <Line
            yAxisId="right"
            dataKey="cumulative"
            name="Cumulative"
            stroke="#1B4965"
            strokeWidth={3}
            dot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
