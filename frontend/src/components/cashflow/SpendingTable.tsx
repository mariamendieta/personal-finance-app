"use client";

import type { CategorySpending } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";

export default function SpendingTable({
  data,
  periodLabel,
  selectedCategory,
  onCategoryClick,
}: {
  data: CategorySpending[];
  periodLabel: string;
  selectedCategory?: string | null;
  onCategoryClick?: (category: string) => void;
}) {
  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">
        Outflows by Category ({periodLabel})
      </h2>
      <div className="overflow-x-auto rounded-lg border border-cool-gray">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-cool-white">
              <th className="text-left px-4 py-3 font-semibold text-stone">Category</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">Total</th>
              <th className="text-right px-4 py-3 font-semibold text-stone">% of Outflows</th>
            </tr>
          </thead>
          <tbody>
            {data.map(row => (
              <tr
                key={row.category}
                onClick={() => onCategoryClick?.(row.category)}
                className={`border-t border-cool-gray cursor-pointer transition-colors ${
                  selectedCategory === row.category
                    ? "bg-azul/10 border-l-2 border-l-azul"
                    : "hover:bg-cool-white/50"
                }`}
              >
                <td className="px-4 py-2.5">{row.category}</td>
                <td className="px-4 py-2.5 text-right font-medium">{formatCurrency(row.total, 2)}</td>
                <td className="px-4 py-2.5 text-right text-stone">{formatPercent(row.percent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
