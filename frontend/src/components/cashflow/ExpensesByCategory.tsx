"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { MonthlyExpense } from "@/lib/api";
import { formatCurrency, formatMonth } from "@/lib/format";

const CATEGORY_ORDER = [
  "Mortgage, Loans & Car", "Childcare", "Taxes & Tax Fees", "Travel",
  "Other Expenses", "Utilities", "House & Maintenance", "Subscriptions",
];

const COLORS: Record<string, string> = {
  "Mortgage, Loans & Car": "#1B4965",
  "Childcare": "#2D6A4F",
  "Taxes & Tax Fees": "#E07A5F",
  "Travel": "#E07A5F",
  "Other Expenses": "#6B5E52",
  "Utilities": "#E9A820",
  "House & Maintenance": "#52B788",
  "Subscriptions": "#9A9A9A",
};

interface ChartRow {
  month: string;
  monthLabel: string;
  total: number;
  [key: string]: number | string | { category: string; amount: number }[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: ChartRow }>; label?: string }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;

  return (
    <div className="bg-white border border-cool-gray rounded-lg shadow-lg p-3 text-sm max-w-xs">
      <p className="font-semibold mb-1">{row.monthLabel}</p>
      <p className="text-stone mb-2">Total: {formatCurrency(row.total)}</p>
      {payload
        .filter(p => p.value > 0)
        .sort((a, b) => b.value - a.value)
        .map(p => {
          const breakdowns = row[`${p.name}_breakdown`] as { category: string; amount: number }[] | undefined;
          return (
            <div key={p.name} className="mb-1">
              <div className="flex justify-between gap-4">
                <span style={{ color: COLORS[p.name] }}>{p.name}</span>
                <span className="font-medium">{formatCurrency(p.value)}</span>
              </div>
              {breakdowns && breakdowns.length > 1 && breakdowns.map(b => (
                <div key={b.category} className="flex justify-between gap-4 ml-3 text-xs text-stone">
                  <span>{b.category}</span>
                  <span>{formatCurrency(b.amount)}</span>
                </div>
              ))}
            </div>
          );
        })}
    </div>
  );
}

export default function ExpensesByCategory({ data }: { data: MonthlyExpense[] }) {
  // Pivot data: one row per month, one key per display_category
  const monthMap = new Map<string, ChartRow>();
  for (const item of data) {
    if (!monthMap.has(item.month)) {
      monthMap.set(item.month, {
        month: item.month,
        monthLabel: formatMonth(item.month),
        total: 0,
      });
    }
    const row = monthMap.get(item.month)!;
    row[item.display_category] = item.amount;
    row[`${item.display_category}_breakdown`] = item.breakdown;
    row.total += item.amount;
  }
  const chartData = Array.from(monthMap.values()).sort((a, b) => a.month.localeCompare(b.month));
  const categories = CATEGORY_ORDER.filter(c => data.some(d => d.display_category === c));

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Monthly Expenses by Category</h2>
      <ResponsiveContainer width="100%" height={450}>
        <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 5, left: 20 }}>
          <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: 8 }} />
          {categories.map(cat => (
            <Bar key={cat} dataKey={cat} stackId="a" fill={COLORS[cat]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
