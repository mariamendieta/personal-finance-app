"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from "recharts";
import type { VendorSpending } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

export default function TopVendorsChart({
  data,
  periodLabel,
}: {
  data: VendorSpending[];
  periodLabel: string;
}) {
  const chartData = [...data].reverse(); // Recharts renders bottom-up for horizontal bars

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Top 10 Vendors ({periodLabel})
      </h2>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 100, bottom: 5, left: 150 }}>
          <XAxis type="number" tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <YAxis type="category" dataKey="vendor" tick={{ fontSize: 13 }} width={140} />
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
            labelFormatter={(label: string) => label}
          />
          <Bar dataKey="total" fill="#1B4965" barSize={24}>
            <LabelList
              dataKey="total"
              position="right"
              formatter={(v: number) => {
                const item = data.find(d => d.total === v);
                return `${formatCurrency(v)} (${item?.percent}%)`;
              }}
              style={{ fontSize: 12, fill: "#2A2522" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
