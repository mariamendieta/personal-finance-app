"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import MetricCard from "@/components/layout/MetricCard";
import Tabs from "@/components/layout/Tabs";
import AssetAllocationPie from "@/components/investments/AssetAllocationPie";
import AccountsPie from "@/components/investments/AccountsPie";
import RetirementVsTaxable from "@/components/investments/RetirementVsTaxable";
import SnapshotComparison from "@/components/investments/SnapshotComparison";
import AddInvestmentsTab from "@/components/investments/AddInvestmentsTab";

export default function InvestmentsPage() {
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });
  const { data: snapshots, isLoading } = useQuery({
    queryKey: ["snapshots"],
    queryFn: api.getSnapshots,
  });

  const [selectedSnapshot, setSelectedSnapshot] = useState<string>("");
  const [compareSnapshot, setCompareSnapshot] = useState<string>("");

  const snapshot = selectedSnapshot || snapshots?.[0] || "";

  const { data: summary } = useQuery({
    queryKey: ["portfolio-summary", snapshot],
    queryFn: () => api.getPortfolioSummary(snapshot),
    enabled: !!snapshot,
  });
  const { data: allocation } = useQuery({
    queryKey: ["asset-allocation", snapshot],
    queryFn: () => api.getAssetAllocation(snapshot),
    enabled: !!snapshot,
  });
  const { data: accounts } = useQuery({
    queryKey: ["by-account", snapshot],
    queryFn: () => api.getByAccount(snapshot),
    enabled: !!snapshot,
  });
  const { data: retVsTax } = useQuery({
    queryKey: ["retirement-vs-taxable", snapshot],
    queryFn: () => api.getRetirementVsTaxable(snapshot),
    enabled: !!snapshot,
  });

  const compTo = compareSnapshot || snapshots?.[1] || "";
  const { data: comparison } = useQuery({
    queryKey: ["comparison", snapshot, compTo],
    queryFn: () => api.getComparison(snapshot, compTo),
    enabled: !!snapshot && !!compTo && snapshot !== compTo,
  });

  // Prior snapshot = chronologically immediately before selected
  const sortedSnaps = [...(snapshots || [])].sort();
  const selectedIdx = sortedSnaps.indexOf(snapshot);
  const priorSnapshot = selectedIdx > 0 ? sortedSnaps[selectedIdx - 1] : "";

  // Prior month snapshot = snapshot closest to 30 days before current
  const priorMonthSnapshot = (() => {
    if (!snapshot) return "";
    const currentMs = new Date(snapshot).getTime();
    const targetMs = currentMs - 30 * 24 * 3600 * 1000;
    const candidates = sortedSnaps.filter(s => new Date(s).getTime() < currentMs);
    if (!candidates.length) return "";
    return candidates.reduce((best, s) =>
      Math.abs(new Date(s).getTime() - targetMs) < Math.abs(new Date(best).getTime() - targetMs) ? s : best
    );
  })();

  // YTD snapshot = earliest snapshot in current year (year of selected)
  const currentYear = snapshot.substring(0, 4);
  const ytdSnapshot = sortedSnaps.find(s => s.startsWith(currentYear)) || "";

  const { data: priorComparison } = useQuery({
    queryKey: ["comparison-prior", snapshot, priorSnapshot],
    queryFn: () => api.getComparison(snapshot, priorSnapshot),
    enabled: !!snapshot && !!priorSnapshot && snapshot !== priorSnapshot,
  });
  const { data: priorMonthComparison } = useQuery({
    queryKey: ["comparison-prior-month", snapshot, priorMonthSnapshot],
    queryFn: () => api.getComparison(snapshot, priorMonthSnapshot),
    enabled: !!snapshot && !!priorMonthSnapshot && snapshot !== priorMonthSnapshot,
  });
  const { data: ytdComparison } = useQuery({
    queryKey: ["comparison-ytd", snapshot, ytdSnapshot],
    queryFn: () => api.getComparison(snapshot, ytdSnapshot),
    enabled: !!snapshot && !!ytdSnapshot && snapshot !== ytdSnapshot,
  });

  const accountCount = accounts?.length || 0;

  const familyName = config?.family_name || "Woffieta Family";

  return (
    <div>
      {/* Header */}
      <div className="pb-2 mb-6 border-b-[3px]"
        style={{ borderImage: "linear-gradient(90deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1" }}>
        <h1 className="font-[Cormorant_Garamond,serif] text-[2.4rem] font-normal text-warm-charcoal leading-tight">
          {familyName}
        </h1>
        <p className="text-[0.85rem] font-light text-stone tracking-[0.1em] uppercase">
          Investments
        </p>
      </div>

      <Tabs tabs={["Dashboard", "Add Data"]}>
        {/* Dashboard tab */}
        <div>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <p className="text-stone text-lg">Loading portfolio data...</p>
            </div>
          ) : !snapshots?.length ? (
            <div className="flex items-center justify-center h-64">
              <p className="text-stone text-lg">No portfolio snapshots found. Upload data in the Add Data tab.</p>
            </div>
          ) : (
            <>
              {/* Snapshot selector */}
              <div className="mb-6">
                <label className="text-sm font-semibold text-stone uppercase tracking-wide mr-3">Snapshot</label>
                <select
                  value={snapshot}
                  onChange={e => setSelectedSnapshot(e.target.value)}
                  className="border border-stone rounded px-3 py-1.5 text-sm text-warm-charcoal"
                >
                  {snapshots.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {summary && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <MetricCard
                    label={`Total Portfolio Value · ${accountCount} accounts`}
                    value={formatCurrency(summary.total_value, 2)}
                    accent="azul"
                  />
                  <MetricCard
                    label={priorSnapshot ? `vs Prior Snapshot (${priorSnapshot})` : "vs Prior Snapshot"}
                    value={priorComparison
                      ? `${formatCurrency(priorComparison.change, 2)} (${priorComparison.pct_change >= 0 ? "+" : ""}${priorComparison.pct_change.toFixed(2)}%)`
                      : "—"}
                    accent={priorComparison && priorComparison.change >= 0 ? "verde" : "coral"}
                  />
                  <MetricCard
                    label={priorMonthSnapshot ? `Prior Month Change (${priorMonthSnapshot})` : "Prior Month Change"}
                    value={priorMonthComparison
                      ? `${formatCurrency(priorMonthComparison.change, 2)} (${priorMonthComparison.pct_change >= 0 ? "+" : ""}${priorMonthComparison.pct_change.toFixed(2)}%)`
                      : "—"}
                    accent={priorMonthComparison && priorMonthComparison.change >= 0 ? "verde" : "coral"}
                  />
                  <MetricCard
                    label={ytdSnapshot ? `YTD (from ${ytdSnapshot})` : "YTD"}
                    value={ytdComparison
                      ? `${formatCurrency(ytdComparison.change, 2)} (${ytdComparison.pct_change >= 0 ? "+" : ""}${ytdComparison.pct_change.toFixed(2)}%)`
                      : "—"}
                    accent={ytdComparison && ytdComparison.change >= 0 ? "verde" : "coral"}
                  />
                </div>
              )}

              <hr className="border-cool-gray mb-8" />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-10">
                {allocation && <AssetAllocationPie data={allocation} />}
                {accounts && <AccountsPie data={accounts} />}
              </div>

              <hr className="border-cool-gray my-8" />

              {retVsTax && <RetirementVsTaxable data={retVsTax} />}

              {snapshots.length > 1 && (
                <>
                  <hr className="border-cool-gray my-8" />
                  <div className="mb-4">
                    <label className="text-sm font-semibold text-stone uppercase tracking-wide mr-3">Compare to</label>
                    <select
                      value={compTo}
                      onChange={e => setCompareSnapshot(e.target.value)}
                      className="border border-stone rounded px-3 py-1.5 text-sm text-warm-charcoal"
                    >
                      {snapshots.filter(s => s !== snapshot).map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                  {comparison && <SnapshotComparison data={comparison} />}
                </>
              )}
            </>
          )}
        </div>

        {/* Add Data tab */}
        <AddInvestmentsTab />
      </Tabs>
    </div>
  );
}
