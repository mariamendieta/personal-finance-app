"use client";

import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import type { MonthlyIncome } from "@/lib/api";
import { formatCurrency, formatMonth } from "@/lib/format";

const PALETTE = ["#1B4965", "#2D6A4F", "#52B788", "#E07A5F", "#E9A820", "#6B5E52"];

export default function IncomeBySource({
  data,
  hiddenSubcategories: controlledHidden,
  onToggleSubcategory,
}: {
  data: MonthlyIncome[];
  hiddenSubcategories?: Set<string>;
  onToggleSubcategory?: (sub: string) => void;
}) {
  const subcategories = [...new Set(data.map(d => d.subcategory))].sort();
  const [internalHidden, setInternalHidden] = useState<Set<string>>(new Set());
  const hidden = controlledHidden ?? internalHidden;

  const toggleSub = (sub: string) => {
    if (onToggleSubcategory) {
      onToggleSubcategory(sub);
      return;
    }
    setInternalHidden(prev => {
      const next = new Set(prev);
      next.has(sub) ? next.delete(sub) : next.add(sub);
      return next;
    });
  };

  const visibleSubs = subcategories.filter(s => !hidden.has(s));

  const monthMap = new Map<string, Record<string, number | string>>();
  for (const item of data) {
    if (hidden.has(item.subcategory)) continue;
    if (!monthMap.has(item.month)) {
      monthMap.set(item.month, { month: item.month, monthLabel: formatMonth(item.month) });
    }
    const row = monthMap.get(item.month)!;
    row[item.subcategory] = item.amount;
  }
  const chartData = Array.from(monthMap.values()).sort((a, b) =>
    (a.month as string).localeCompare(b.month as string)
  );
  const avgIncome = chartData.length > 0
    ? chartData.reduce((sum, row) => {
        const total = visibleSubs.reduce((s, sub) => s + (Number(row[sub]) || 0), 0);
        return sum + total;
      }, 0) / chartData.length
    : 0;

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Monthly Inflows by Source</h2>
      <div className="flex flex-wrap gap-2 mb-4">
        {subcategories.map((sub, i) => {
          const color = PALETTE[i % PALETTE.length];
          const isHidden = hidden.has(sub);
          return (
            <button
              key={sub}
              onClick={() => toggleSub(sub)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                isHidden
                  ? "border-cool-gray text-stone bg-cool-white line-through opacity-50"
                  : "border-current font-medium"
              }`}
              style={{ color: isHidden ? undefined : color, borderColor: isHidden ? undefined : color }}
            >
              {sub}
            </button>
          );
        })}
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 5, left: 20 }}>
          <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
            labelFormatter={(label: string) => label}
          />
          <Legend wrapperStyle={{ paddingTop: 8 }} />
          {visibleSubs.map((sub) => {
            const i = subcategories.indexOf(sub);
            return <Bar key={sub} dataKey={sub} stackId="a" fill={PALETTE[i % PALETTE.length]} />;
          })}
          {avgIncome > 0 && (
            <ReferenceLine
              y={avgIncome}
              stroke="#2D6A4F"
              strokeDasharray="6 4"
              strokeWidth={2}
              label={{ value: `Avg: ${formatCurrency(avgIncome)}`, position: "left", fontSize: 12, fill: "#2D6A4F" }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
