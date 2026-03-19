"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { RetirementVsTaxable as RVT } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function RetirementVsTaxable({ data }: { data: RVT }) {
  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Asset Class: Retirement vs Taxable
      </h2>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-cool-gray mb-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-cool-white">
              <th className="text-left px-4 py-3 font-semibold text-stone">Asset Class</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Retirement</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">% of Ret.</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Taxable</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">% of Tax.</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Total</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">% Portfolio</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map(row => (
              <tr key={row.asset_class} className="border-t border-cool-gray hover:bg-cool-white/50">
                <td className="px-4 py-2.5 font-medium">{row.asset_class}</td>
                <td className="px-4 py-2.5 text-right">{formatCurrency(row.retirement)}</td>
                <td className="px-4 py-2.5 text-right text-stone">{formatPercent(row.pct_retirement)}</td>
                <td className="px-4 py-2.5 text-right">{formatCurrency(row.taxable)}</td>
                <td className="px-4 py-2.5 text-right text-stone">{formatPercent(row.pct_taxable)}</td>
                <td className="px-4 py-2.5 text-right font-medium">{formatCurrency(row.total)}</td>
                <td className="px-4 py-2.5 text-right text-stone">{formatPercent(row.pct_portfolio)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Grouped bar chart */}
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data.rows} margin={{ top: 20, right: 20, bottom: 5, left: 20 }}>
          <XAxis dataKey="asset_class" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
          <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip formatter={(value: number) => formatCurrency(value)} />
          <Legend wrapperStyle={{ paddingTop: 8 }} />
          <Bar dataKey="retirement" name="Retirement" fill="#1B4965" />
          <Bar dataKey="taxable" name="Taxable" fill="#E07A5F" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
