"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { MonthlyIncome } from "@/lib/api";
import { formatCurrency, formatMonth } from "@/lib/format";

const PALETTE = ["#1B4965", "#2D6A4F", "#52B788", "#E07A5F", "#E9A820", "#6B5E52"];

export default function IncomeBySource({ data }: { data: MonthlyIncome[] }) {
  // Get unique subcategories
  const subcategories = [...new Set(data.map(d => d.subcategory))];

  // Pivot: one row per month
  const monthMap = new Map<string, Record<string, number | string>>();
  for (const item of data) {
    if (!monthMap.has(item.month)) {
      monthMap.set(item.month, { month: item.month, monthLabel: formatMonth(item.month) });
    }
    const row = monthMap.get(item.month)!;
    row[item.subcategory] = item.amount;
  }
  const chartData = Array.from(monthMap.values()).sort((a, b) =>
    (a.month as string).localeCompare(b.month as string)
  );

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Monthly Income by Source</h2>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 5, left: 20 }}>
          <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
            labelFormatter={(label: string) => label}
          />
          <Legend wrapperStyle={{ paddingTop: 8 }} />
          {subcategories.map((sub, i) => (
            <Bar key={sub} dataKey={sub} stackId="a" fill={PALETTE[i % PALETTE.length]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
