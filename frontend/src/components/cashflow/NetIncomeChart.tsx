"use client";

import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell,
} from "recharts";
import type { NetIncomeMonth } from "@/lib/api";
import { formatCurrency, formatMonth } from "@/lib/format";

export default function NetIncomeChart({ data }: { data: NetIncomeMonth[] }) {
  const chartData = data.map(d => ({
    ...d,
    monthLabel: formatMonth(d.month),
  }));

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Net Income per Month &amp; Cumulative
      </h2>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 60, bottom: 5, left: 20 }}>
          <XAxis dataKey="monthLabel" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="left"
            tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            label={{ value: "Monthly Net ($)", angle: -90, position: "insideLeft", offset: -5, style: { fontSize: 12 } }}
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
