"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import MetricCard from "@/components/layout/MetricCard";
import Tabs from "@/components/layout/Tabs";
import ExpensesByCategory from "@/components/cashflow/ExpensesByCategory";
import IncomeBySource from "@/components/cashflow/IncomeBySource";
import NetIncomeChart from "@/components/cashflow/NetIncomeChart";
import SpendingTable from "@/components/cashflow/SpendingTable";
import TopVendorsChart from "@/components/cashflow/TopVendorsChart";
import AddCashFlowTab from "@/components/cashflow/AddCashFlowTab";

export default function CashFlowPage() {
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["cashflow-summary"],
    queryFn: () => api.getCashFlowSummary(12),
  });
  const { data: expenses } = useQuery({
    queryKey: ["monthly-expenses"],
    queryFn: () => api.getMonthlyExpenses(12),
  });
  const { data: income } = useQuery({
    queryKey: ["monthly-income"],
    queryFn: () => api.getMonthlyIncome(12),
  });
  const { data: netIncome } = useQuery({
    queryKey: ["net-income"],
    queryFn: () => api.getNetIncome(12),
  });
  const { data: categories } = useQuery({
    queryKey: ["spending-by-category"],
    queryFn: () => api.getSpendingByCategory(12),
  });
  const { data: vendors } = useQuery({
    queryKey: ["top-vendors"],
    queryFn: () => api.getTopVendors(12),
  });

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
          Cash Flow
        </p>
      </div>

      <Tabs tabs={["Dashboard", "Add Data"]}>
        {/* Dashboard tab */}
        <div>
          {loadingSummary ? (
            <div className="flex items-center justify-center h-64">
              <p className="text-stone text-lg">Loading cash flow data...</p>
            </div>
          ) : (
            <>
              {summary && (
                <div className="grid grid-cols-3 gap-6 mb-8">
                  <MetricCard label="Total Income (12 mo)" value={formatCurrency(summary.total_income)} accent="azul" />
                  <MetricCard label="Total Spending (12 mo)" value={formatCurrency(summary.total_spending)} accent="coral" />
                  <MetricCard label="Net Income (12 mo)" value={formatCurrency(summary.net_income)} accent="verde" />
                </div>
              )}

              <hr className="border-cool-gray mb-8" />

              {expenses && <ExpensesByCategory data={expenses} />}
              <div className="mt-10" />
              {income && <IncomeBySource data={income} />}
              <div className="mt-10" />
              {netIncome && <NetIncomeChart data={netIncome} />}

              <hr className="border-cool-gray my-8" />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <div>{categories && <SpendingTable data={categories} periodLabel="Last 12 months" />}</div>
                <div>{vendors && <TopVendorsChart data={vendors} periodLabel="Last 12 months" />}</div>
              </div>
            </>
          )}
        </div>

        {/* Add Data tab */}
        <AddCashFlowTab />
      </Tabs>
    </div>
  );
}
