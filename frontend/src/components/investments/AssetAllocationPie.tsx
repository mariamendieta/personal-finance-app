"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { AssetAllocation } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";

const PALETTE = ["#1B4965", "#2D6A4F", "#52B788", "#E07A5F", "#E9A820", "#6B5E52"];

export default function AssetAllocationPie({
  data,
  title = "Asset Class Allocation",
}: {
  data: AssetAllocation[];
  title?: string;
}) {
  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">{title}</h2>
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="asset_class"
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={130}
            label={({ asset_class, percent }) => `${asset_class} ${formatPercent(percent)}`}
            labelLine={{ strokeWidth: 1 }}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => formatCurrency(value)}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
