"use client";

import { useState, useCallback } from "react";
import PipelineRunner from "@/components/upload/PipelineRunner";

const CREDIT_CARDS = [
  { label: "Aeroplan (Chase)", filePrefix: "Aeroplan" },
  { label: "AmazonPrime (Chase)", filePrefix: "AmazonPrime" },
  { label: "United (Chase)", filePrefix: "United" },
  { label: "VentureX (Capital One)", filePrefix: "VentureX" },
  { label: "VentureOne (Capital One)", filePrefix: "VentureOne" },
  { label: "Alaska (BofA)", filePrefix: "Alaska" },
];

const BANK_ACCOUNTS = [
  { label: "SoFi Joint Checking", filePrefix: "SOFI-JointChecking" },
  { label: "SoFi Joint Savings", filePrefix: "SOFI-JointSavings" },
  { label: "BoA Checking", filePrefix: "BoA-Checking" },
  { label: "BoA Savings", filePrefix: "BoA-Savings" },
  { label: "Chase Checking", filePrefix: "Chase-Checking" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getMonthOptions() {
  const today = new Date();
  const options = [];
  for (let offset = 0; offset < 6; offset++) {
    const d = new Date(today.getFullYear(), today.getMonth() - offset, 1);
    const label = d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    const monthAbbr = d.toLocaleDateString("en-US", { month: "short" });
    const folder = `${monthAbbr}${String(d.getFullYear()).slice(-2)}`;
    options.push({ label, folder });
  }
  return options;
}

export default function AddCashFlowTab() {
  const monthOptions = getMonthOptions();
  const [selectedMonth, setSelectedMonth] = useState(monthOptions[0].folder);
  const [ccFiles, setCcFiles] = useState<Map<string, File>>(new Map());
  const [bankFiles, setBankFiles] = useState<Map<string, File>>(new Map());
  const [otherFiles, setOtherFiles] = useState<File[]>([]);
  const [otherType, setOtherType] = useState<"Credit Cards" | "Checking and Savings">("Credit Cards");
  const [runPipeline, setRunPipeline] = useState(true);
  const [runReport, setRunReport] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<{ script: string; success: boolean; output: string }[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  const totalFiles = ccFiles.size + bankFiles.size + otherFiles.length;

  const handleSubmit = useCallback(async () => {
    setIsRunning(true);
    setResults([]);
    setSavedCount(0);

    for (const [prefix, file] of ccFiles) {
      const formData = new FormData();
      formData.append("month_folder", selectedMonth);
      formData.append("subfolder", "Credit Cards");
      formData.append("run_pipeline", "false");
      formData.append("run_report", "false");
      const renamedFile = new File([file], `${prefix}_${selectedMonth}.csv`, { type: file.type });
      formData.append("files", renamedFile);
      await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
    }

    for (const [prefix, file] of bankFiles) {
      const formData = new FormData();
      formData.append("month_folder", selectedMonth);
      formData.append("subfolder", "Checking and Savings");
      formData.append("run_pipeline", "false");
      formData.append("run_report", "false");
      const renamedFile = new File([file], `${prefix}_${selectedMonth}.csv`, { type: file.type });
      formData.append("files", renamedFile);
      await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
    }

    if (otherFiles.length > 0) {
      const formData = new FormData();
      formData.append("month_folder", selectedMonth);
      formData.append("subfolder", otherType);
      formData.append("run_pipeline", "false");
      formData.append("run_report", "false");
      for (const f of otherFiles) {
        formData.append("files", f);
      }
      await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
    }

    setSavedCount(totalFiles);

    if (runPipeline || runReport) {
      const formData = new FormData();
      formData.append("month_folder", selectedMonth);
      formData.append("subfolder", "Credit Cards");
      formData.append("run_pipeline", String(runPipeline));
      formData.append("run_report", String(runReport));
      formData.append("files", new File([""], ".placeholder.csv", { type: "text/csv" }));

      const res = await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
      const data = await res.json();
      setResults(data.pipeline_results || []);
    }

    setIsRunning(false);
  }, [ccFiles, bankFiles, otherFiles, otherType, selectedMonth, runPipeline, runReport, totalFiles]);

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Upload Cash Flow Data</h2>
      <p className="text-sm text-stone mb-6">Upload your monthly CSV exports and run the cash flow pipeline.</p>

      {/* Month selector */}
      <div className="mb-6">
        <label className="text-sm font-semibold text-stone uppercase tracking-wide mr-3">Month</label>
        <select
          value={selectedMonth}
          onChange={e => setSelectedMonth(e.target.value)}
          className="border border-stone rounded px-3 py-1.5 text-sm text-warm-charcoal"
        >
          {monthOptions.map(m => (
            <option key={m.folder} value={m.folder}>{m.label}</option>
          ))}
        </select>
      </div>

      <hr className="border-cool-gray mb-6" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div>
          <h3 className="font-semibold text-warm-charcoal mb-3">Credit Cards</h3>
          <div className="space-y-3">
            {CREDIT_CARDS.map(({ label, filePrefix }) => (
              <div key={filePrefix} className="flex items-center gap-3">
                <label className="text-sm text-stone w-44 shrink-0">{label}</label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={e => {
                    const f = e.target.files?.[0];
                    setCcFiles(prev => {
                      const next = new Map(prev);
                      f ? next.set(filePrefix, f) : next.delete(filePrefix);
                      return next;
                    });
                  }}
                  className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
                />
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="font-semibold text-warm-charcoal mb-3">Checking & Savings</h3>
          <div className="space-y-3">
            {BANK_ACCOUNTS.map(({ label, filePrefix }) => (
              <div key={filePrefix} className="flex items-center gap-3">
                <label className="text-sm text-stone w-44 shrink-0">{label}</label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={e => {
                    const f = e.target.files?.[0];
                    setBankFiles(prev => {
                      const next = new Map(prev);
                      f ? next.set(filePrefix, f) : next.delete(filePrefix);
                      return next;
                    });
                  }}
                  className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
                />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Other files */}
      <div className="mb-8">
        <h3 className="font-semibold text-warm-charcoal mb-3">Other Cash Flow Files</h3>
        <p className="text-xs text-stone mb-2">Upload additional CSVs with their original filenames.</p>
        <div className="flex items-center gap-4 mb-2">
          <input
            type="file"
            accept=".csv"
            multiple
            onChange={e => setOtherFiles(Array.from(e.target.files || []))}
            className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
          />
          <label className="text-sm text-stone">Save to:</label>
          <select
            value={otherType}
            onChange={e => setOtherType(e.target.value as typeof otherType)}
            className="border border-stone rounded px-2 py-1 text-sm"
          >
            <option>Credit Cards</option>
            <option>Checking and Savings</option>
          </select>
        </div>
      </div>

      <hr className="border-cool-gray mb-6" />

      <h3 className="font-semibold text-warm-charcoal mb-3">Run Pipeline</h3>
      <div className="bg-cool-white rounded-lg px-4 py-3 mb-4 text-sm text-stone">
        Ready: <span className="font-semibold text-warm-charcoal">{totalFiles}</span> cash flow file(s)
      </div>

      <div className="flex items-center gap-6 mb-4">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={runPipeline} onChange={e => setRunPipeline(e.target.checked)} className="accent-azul" />
          Run Cash Flow pipeline
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={runReport} onChange={e => setRunReport(e.target.checked)} className="accent-azul" />
          Generate Excel report
        </label>
      </div>

      <button
        onClick={handleSubmit}
        disabled={totalFiles === 0 || isRunning}
        className="bg-azul text-white px-6 py-2.5 rounded font-semibold text-sm hover:bg-verde-claro disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isRunning ? "Running..." : "Save Files & Run"}
      </button>

      <PipelineRunner results={results} savedCount={savedCount} isRunning={isRunning} />
    </div>
  );
}
