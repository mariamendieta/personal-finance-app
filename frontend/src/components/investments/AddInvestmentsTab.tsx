"use client";

import { useState, useCallback } from "react";
import PipelineRunner from "@/components/upload/PipelineRunner";

const PORTFOLIO_FILES = [
  { label: "Chase Taxable Brokerage", filename: "ChaseTaxableBrokerage.csv" },
  { label: "Chase Parametric", filename: "ChaseParametric.csv" },
  { label: "Scott's Roth IRA (Chase)", filename: "ScottsRothIRA_Chase.csv" },
  { label: "Scott's Traditional IRA", filename: "ScottsTraditionalIRA.csv" },
  { label: "SoFi Joint", filename: "SOFI_Joint.csv" },
  { label: "SoFi Self-Directed", filename: "SOFI_SelfDirected.csv" },
  { label: "Maria's Roth IRA", filename: "Marias Roth IRA.csv" },
  { label: "Maria Carbon Direct 401k", filename: "Maria Carbon Direct 401k.csv" },
  { label: "Maria Accrue LevelTen 401k", filename: "Maria Accrue LevelTen 401k.csv" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AddInvestmentsTab() {
  const today = new Date().toISOString().split("T")[0];
  const [snapshotDate, setSnapshotDate] = useState(today);
  const [files, setFiles] = useState<Map<string, File>>(new Map());
  const [otherFiles, setOtherFiles] = useState<File[]>([]);
  const [runAnalysis, setRunAnalysis] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<{ script: string; success: boolean; output: string }[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  const totalFiles = files.size + otherFiles.length;

  const handleSubmit = useCallback(async () => {
    setIsRunning(true);
    setResults([]);
    setSavedCount(0);

    const formData = new FormData();
    formData.append("snapshot_date", snapshotDate);
    formData.append("run_analysis", String(runAnalysis));

    for (const [filename, file] of files) {
      formData.append("files", new File([file], filename, { type: file.type }));
    }
    for (const f of otherFiles) {
      formData.append("files", f);
    }

    const res = await fetch(`${API_BASE}/api/upload/portfolio`, { method: "POST", body: formData });
    const data = await res.json();

    setSavedCount(data.saved_count || 0);
    setResults(data.pipeline_results || []);
    setIsRunning(false);
  }, [files, otherFiles, snapshotDate, runAnalysis]);

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Upload Investment Data</h2>
      <p className="text-sm text-stone mb-6">Upload your portfolio CSV exports and run the portfolio analysis.</p>

      <div className="mb-6">
        <label className="text-sm font-semibold text-stone uppercase tracking-wide mr-3">Snapshot Date</label>
        <input
          type="date"
          value={snapshotDate}
          onChange={e => setSnapshotDate(e.target.value)}
          className="border border-stone rounded px-3 py-1.5 text-sm text-warm-charcoal"
        />
      </div>

      <hr className="border-cool-gray mb-6" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-3 mb-8">
        {PORTFOLIO_FILES.map(({ label, filename }) => (
          <div key={filename} className="flex items-center gap-3">
            <label className="text-sm text-stone w-44 shrink-0">{label}</label>
            <input
              type="file"
              accept=".csv"
              onChange={e => {
                const f = e.target.files?.[0];
                setFiles(prev => {
                  const next = new Map(prev);
                  f ? next.set(filename, f) : next.delete(filename);
                  return next;
                });
              }}
              className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
            />
          </div>
        ))}
      </div>

      <div className="mb-8">
        <h3 className="font-semibold text-warm-charcoal mb-3">Other Investment Files</h3>
        <p className="text-xs text-stone mb-2">Upload additional CSVs (saved with original filename).</p>
        <input
          type="file"
          accept=".csv"
          multiple
          onChange={e => setOtherFiles(Array.from(e.target.files || []))}
          className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray"
        />
      </div>

      <hr className="border-cool-gray mb-6" />

      <h3 className="font-semibold text-warm-charcoal mb-3">Run Pipeline</h3>
      <div className="bg-cool-white rounded-lg px-4 py-3 mb-4 text-sm text-stone">
        Ready: <span className="font-semibold text-warm-charcoal">{totalFiles}</span> portfolio file(s)
      </div>

      <label className="flex items-center gap-2 text-sm mb-4">
        <input type="checkbox" checked={runAnalysis} onChange={e => setRunAnalysis(e.target.checked)} className="accent-azul" />
        Run Portfolio analysis
      </label>

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
