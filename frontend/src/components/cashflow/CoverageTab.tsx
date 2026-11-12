"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatMonthLabel(yyyyMm: string) {
  // "2026-10" -> "Oct 26"
  const [y, m] = yyyyMm.split("-").map(Number);
  return `${MONTH_ABBR[m - 1]} ${String(y).slice(-2)}`;
}

function CoverageRow({
  name,
  months,
  present,
}: {
  name: string;
  months: string[];
  present: Set<string>;
}) {
  const coveredCount = months.filter(m => present.has(m)).length;
  return (
    <tr className="border-b border-cool-gray">
      <td className="py-2 pr-4 text-sm text-warm-charcoal whitespace-nowrap sticky left-0 bg-white">
        {name}
      </td>
      {months.map(m => (
        <td key={m} className="text-center px-1">
          {present.has(m) ? (
            <span className="inline-block w-5 h-5 rounded-full bg-verde-claro/20 text-verde-hoja text-xs leading-5">✓</span>
          ) : (
            <span className="inline-block w-5 h-5 rounded-full bg-coral/10 text-coral text-xs leading-5">—</span>
          )}
        </td>
      ))}
      <td className="text-center text-xs text-stone pl-2">
        {coveredCount}/{months.length}
      </td>
    </tr>
  );
}

export default function CoverageTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["cashflow-coverage"],
    queryFn: () => api.getCashflowCoverage(),
  });

  if (isLoading) {
    return <p className="text-sm text-stone">Loading coverage...</p>;
  }
  if (!data || data.months.length === 0) {
    return <p className="text-sm text-stone">No cash flow data found yet.</p>;
  }

  const { months, accounts, coverage } = data;
  const creditCards = accounts.filter(a => a.subfolder === "Credit Cards");
  const bankAccounts = accounts.filter(a => a.subfolder === "Checking and Savings");

  const renderSection = (title: string, list: typeof accounts) => (
    <div className="mb-8">
      <h3 className="font-semibold text-warm-charcoal mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-cool-gray">
              <th className="text-left py-2 pr-4 text-xs text-stone sticky left-0 bg-white">Account</th>
              {months.map(m => (
                <th key={m} className="text-center px-1 text-xs text-stone whitespace-nowrap">
                  {formatMonthLabel(m)}
                </th>
              ))}
              <th className="text-center text-xs text-stone pl-2">Coverage</th>
            </tr>
          </thead>
          <tbody>
            {list.map(a => (
              <CoverageRow
                key={a.name}
                name={a.name}
                months={months}
                present={new Set(coverage[a.name] ?? [])}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-1">Upload Coverage</h2>
      <p className="text-sm text-stone mb-6">
        Every account that has ever appeared in an uploaded file, and which calendar months actually have a transaction dated that month — based on real transaction dates, not which folder a file sits in. ✓ = at least one transaction that month; — = a gap.
      </p>
      {renderSection("Credit Cards", creditCards)}
      {renderSection("Checking & Savings", bankAccounts)}
    </div>
  );
}
