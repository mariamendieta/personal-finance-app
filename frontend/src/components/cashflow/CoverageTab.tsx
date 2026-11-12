"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, CoverageAccount } from "@/lib/api";

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
  ignored,
  onToggleIgnored,
}: {
  name: string;
  months: string[];
  present: Set<string>;
  ignored: boolean;
  onToggleIgnored: (next: boolean) => void;
}) {
  const coveredCount = months.filter(m => present.has(m)).length;
  return (
    <tr className={`border-b border-cool-gray ${ignored ? "opacity-50" : ""}`}>
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
      <td className="text-center pl-3">
        <label className="flex items-center gap-1 text-xs text-stone whitespace-nowrap cursor-pointer">
          <input
            type="checkbox"
            checked={ignored}
            onChange={e => onToggleIgnored(e.target.checked)}
            className="accent-azul"
          />
          Not used
        </label>
      </td>
    </tr>
  );
}

export default function CoverageTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["cashflow-coverage"],
    queryFn: () => api.getCashflowCoverage(),
  });

  const handleToggleIgnored = async (accountName: string, next: boolean) => {
    await api.setCoverageIgnored(accountName, next);
    queryClient.invalidateQueries({ queryKey: ["cashflow-coverage"] });
  };

  if (isLoading) {
    return <p className="text-sm text-stone">Loading coverage...</p>;
  }
  if (!data || data.months.length === 0) {
    return <p className="text-sm text-stone">No cash flow data found yet.</p>;
  }

  const { months, accounts, coverage } = data;

  const renderSection = (title: string, list: CoverageAccount[]) => {
    const active = list.filter(a => !a.ignored);
    const ignored = list.filter(a => a.ignored);

    const table = (rows: CoverageAccount[]) => (
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
              <th className="text-center text-xs text-stone pl-3">&nbsp;</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(a => (
              <CoverageRow
                key={a.name}
                name={a.name}
                months={months}
                present={new Set(coverage[a.name] ?? [])}
                ignored={a.ignored}
                onToggleIgnored={next => handleToggleIgnored(a.name, next)}
              />
            ))}
          </tbody>
        </table>
      </div>
    );

    return (
      <div className="mb-8">
        <h3 className="font-semibold text-warm-charcoal mb-3">{title}</h3>
        {table(active)}
        {ignored.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-stone mb-2">Not used — excluded from gap tracking:</p>
            {table(ignored)}
          </div>
        )}
      </div>
    );
  };

  const creditCards = accounts.filter(a => a.subfolder === "Credit Cards");
  const bankAccounts = accounts.filter(a => a.subfolder === "Checking and Savings");

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-1">Upload Coverage</h2>
      <p className="text-sm text-stone mb-6">
        Every account that has ever appeared in an uploaded file, and which calendar months actually have a transaction dated that month — based on real transaction dates, not which folder a file sits in. ✓ = at least one transaction that month; — = a gap. Check &quot;Not used&quot; for a card or account you&apos;ve stopped using, so its gaps stop showing up here.
      </p>
      {renderSection("Credit Cards", creditCards)}
      {renderSection("Checking & Savings", bankAccounts)}
    </div>
  );
}
