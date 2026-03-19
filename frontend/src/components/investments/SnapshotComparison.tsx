"use client";

import type { PortfolioComparison } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";
import MetricCard from "@/components/layout/MetricCard";

export default function SnapshotComparison({ data }: { data: PortfolioComparison }) {
  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Portfolio Changes Over Time
      </h2>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <MetricCard label={`Value (${data.previous_snapshot})`} value={formatCurrency(data.previous_total)} />
        <MetricCard label={`Value (${data.current_snapshot})`} value={formatCurrency(data.current_total)} />
        <MetricCard
          label="Change"
          value={`${formatCurrency(data.change)} (${data.pct_change >= 0 ? "+" : ""}${formatPercent(data.pct_change)})`}
          accent={data.change >= 0 ? "verde" : "coral"}
        />
      </div>

      <div className="overflow-x-auto rounded-lg border border-cool-gray">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-cool-white">
              <th className="text-left px-4 py-3 font-semibold text-stone">Asset Class</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Previous</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Current</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Change</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Change %</th>
            </tr>
          </thead>
          <tbody>
            {data.by_asset_class.map(row => (
              <tr key={row.asset_class} className="border-t border-cool-gray hover:bg-cool-white/50">
                <td className="px-4 py-2.5 font-medium">{row.asset_class}</td>
                <td className="px-4 py-2.5 text-right">{formatCurrency(row.previous)}</td>
                <td className="px-4 py-2.5 text-right">{formatCurrency(row.current)}</td>
                <td className={`px-4 py-2.5 text-right font-medium ${row.change >= 0 ? "text-verde-hoja" : "text-coral"}`}>
                  {formatCurrency(row.change)}
                </td>
                <td className={`px-4 py-2.5 text-right ${row.change_pct >= 0 ? "text-verde-hoja" : "text-coral"}`}>
                  {row.change_pct >= 0 ? "+" : ""}{formatPercent(row.change_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
