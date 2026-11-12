"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Account } from "@/lib/api";
import PipelineRunner from "@/components/upload/PipelineRunner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function todayStr() {
  return new Date().toISOString().split("T")[0];
}

function currentMonthFolder() {
  const today = new Date();
  const monthAbbr = today.toLocaleDateString("en-US", { month: "short" });
  return `${monthAbbr}${String(today.getFullYear()).slice(-2)}`;
}

export default function AddCashFlowTab() {
  const thisMonth = currentMonthFolder();
  const [monthFolder, setMonthFolder] = useState(thisMonth);
  const balanceDate = todayStr();
  const queryClient = useQueryClient();

  // Real month folders already on disk, most recent first. The two naming
  // conventions in use ("2026-10_Oct" and "Nov26") are resolved server-side,
  // so this always points at the actual folder for that month, never a
  // disconnected duplicate.
  const { data: existingMonths } = useQuery({
    queryKey: ["cashflow-months"],
    queryFn: () => api.listCashflowMonths(),
  });
  const monthOptions = existingMonths?.includes(thisMonth)
    ? existingMonths
    : [thisMonth, ...(existingMonths ?? [])];

  // Load accounts from API
  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.getAccounts(),
  });

  const allCreditCards = accountsData?.credit_cards ?? [];
  const allBankAccounts = accountsData?.bank_accounts ?? [];

  // Visible accounts (not hidden)
  const ccAccounts = allCreditCards.filter(a => !a.hidden);
  const bankAccounts = allBankAccounts.filter(a => !a.hidden);

  const [ccFiles, setCcFiles] = useState<Map<string, File[]>>(new Map());
  const [bankFiles, setBankFiles] = useState<Map<string, File[]>>(new Map());
  const [otherFiles, setOtherFiles] = useState<File[]>([]);

  const handleMonthChange = (newMonth: string) => {
    setMonthFolder(newMonth);
    // Pending (not-yet-uploaded) selections are for the old month's folder — drop them.
    setCcFiles(new Map());
    setBankFiles(new Map());
    setOtherFiles([]);
  };
  const [otherType, setOtherType] = useState<"Credit Cards" | "Checking and Savings">("Credit Cards");
  const [runPipeline, setRunPipeline] = useState(true);
  const [runReport, setRunReport] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<{ script: string; success: boolean; output: string }[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  // Balances
  const [balances, setBalances] = useState<Record<string, string>>({});
  const [balancesSaved, setBalancesSaved] = useState(false);

  // Add account forms
  const [showAddCC, setShowAddCC] = useState(false);
  const [newCCLabel, setNewCCLabel] = useState("");
  const [newCCPrefix, setNewCCPrefix] = useState("");
  const [showAddBank, setShowAddBank] = useState(false);
  const [newBankLabel, setNewBankLabel] = useState("");
  const [newBankPrefix, setNewBankPrefix] = useState("");

  // Manage accounts toggle
  const [showManageAccounts, setShowManageAccounts] = useState(false);

  // Load existing balances
  const { data: existingBalances } = useQuery({
    queryKey: ["balances", balanceDate],
    queryFn: () => api.getBalances(balanceDate),
  });

  useEffect(() => {
    if (existingBalances) {
      const strBalances: Record<string, string> = {};
      for (const [k, v] of Object.entries(existingBalances)) {
        strBalances[k] = String(v);
      }
      setBalances(strBalances);
      setBalancesSaved(false);
    }
  }, [existingBalances]);

  // Files already saved to disk for this month (from a previous upload)
  const { data: savedFiles } = useQuery({
    queryKey: ["cashflow-files", monthFolder],
    queryFn: () => api.listCashflowFiles(monthFolder),
  });
  const [deletingFile, setDeletingFile] = useState<string | null>(null);

  const handleDeleteSavedFile = async (subfolder: "Credit Cards" | "Checking and Savings", filename: string) => {
    if (!window.confirm(`Delete ${filename}? This removes it from disk — you'll need to re-upload it if that was a mistake.`)) {
      return;
    }
    setDeletingFile(filename);
    await api.deleteCashflowFile(monthFolder, subfolder, filename);
    queryClient.invalidateQueries({ queryKey: ["cashflow-files", monthFolder] });
    setDeletingFile(null);
  };

  const pendingFileCount = (map: Map<string, File[]>) =>
    Array.from(map.values()).reduce((sum, files) => sum + files.length, 0);
  const totalFiles = pendingFileCount(ccFiles) + pendingFileCount(bankFiles) + otherFiles.length;
  const hasBalances = Object.values(balances).some(v => v && parseFloat(v) > 0);

  const handleAddCC = async () => {
    if (!newCCLabel.trim()) return;
    const prefix = newCCPrefix.trim() || newCCLabel.trim().replace(/[^a-zA-Z0-9]/g, "-");
    await api.addAccount("credit_cards", newCCLabel.trim(), prefix);
    queryClient.invalidateQueries({ queryKey: ["accounts"] });
    setNewCCLabel("");
    setNewCCPrefix("");
    setShowAddCC(false);
  };

  const handleAddBank = async () => {
    if (!newBankLabel.trim()) return;
    const prefix = newBankPrefix.trim() || newBankLabel.trim().replace(/[^a-zA-Z0-9]/g, "-");
    await api.addAccount("bank_accounts", newBankLabel.trim(), prefix);
    queryClient.invalidateQueries({ queryKey: ["accounts"] });
    setNewBankLabel("");
    setNewBankPrefix("");
    setShowAddBank(false);
  };

  const handleToggleAccount = async (accountType: string, filePrefix: string, hidden: boolean) => {
    await api.toggleAccount(accountType, filePrefix, hidden);
    queryClient.invalidateQueries({ queryKey: ["accounts"] });
  };

  const handleSubmit = useCallback(async () => {
    setIsRunning(true);
    setResults([]);
    setSavedCount(0);
    setBalancesSaved(false);

    // Save balances with the exact date
    const numBalances: Record<string, number> = {};
    for (const [account, val] of Object.entries(balances)) {
      const num = parseFloat(val);
      if (!isNaN(num) && num > 0) {
        numBalances[account] = num;
      }
    }
    if (Object.keys(numBalances).length > 0) {
      await api.saveBalances(balanceDate, numBalances);
      setBalancesSaved(true);
    }

    // Upload credit card files — multiple files per account get distinct names
    // (prefix_month.csv, prefix_month_2.csv, ...) so they don't overwrite each other.
    for (const [prefix, files] of ccFiles) {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append("month_folder", monthFolder);
        formData.append("subfolder", "Credit Cards");
        formData.append("run_pipeline", "false");
        formData.append("run_report", "false");
        const suffix = i === 0 ? "" : `_${i + 1}`;
        const renamedFile = new File([files[i]], `${prefix}_${monthFolder}${suffix}.csv`, { type: files[i].type });
        formData.append("files", renamedFile);
        await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
      }
    }

    // Upload bank files — same multi-file naming as above
    for (const [prefix, files] of bankFiles) {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append("month_folder", monthFolder);
        formData.append("subfolder", "Checking and Savings");
        formData.append("run_pipeline", "false");
        formData.append("run_report", "false");
        const suffix = i === 0 ? "" : `_${i + 1}`;
        const renamedFile = new File([files[i]], `${prefix}_${monthFolder}${suffix}.csv`, { type: files[i].type });
        formData.append("files", renamedFile);
        await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
      }
    }

    // Upload other files
    if (otherFiles.length > 0) {
      const formData = new FormData();
      formData.append("month_folder", monthFolder);
      formData.append("subfolder", otherType);
      formData.append("run_pipeline", "false");
      formData.append("run_report", "false");
      for (const f of otherFiles) {
        formData.append("files", f);
      }
      await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
    }

    setSavedCount(totalFiles);
    setCcFiles(new Map());
    setBankFiles(new Map());
    setOtherFiles([]);
    queryClient.invalidateQueries({ queryKey: ["cashflow-files", monthFolder] });

    // Run pipeline
    if (runPipeline || runReport) {
      const formData = new FormData();
      formData.append("month_folder", monthFolder);
      formData.append("subfolder", "Credit Cards");
      formData.append("run_pipeline", String(runPipeline));
      formData.append("run_report", String(runReport));
      formData.append("files", new File([""], ".placeholder.csv", { type: "text/csv" }));

      const res = await fetch(`${API_BASE}/api/upload/cashflow`, { method: "POST", body: formData });
      const data = await res.json();
      setResults(data.pipeline_results || []);
    }

    setIsRunning(false);
  }, [ccFiles, bankFiles, otherFiles, otherType, monthFolder, runPipeline, runReport, totalFiles, balances, balanceDate, queryClient]);

  const renderAccountToggle = (account: Account, accountType: string) => (
    <div
      key={`${accountType}-${account.filePrefix}`}
      className={`flex items-center justify-between px-3 py-2 rounded-lg border ${
        account.hidden ? "border-cool-gray bg-cool-white opacity-60" : "border-cool-gray bg-white"
      }`}
    >
      <span className={`text-sm ${account.hidden ? "text-stone line-through" : "text-warm-charcoal"}`}>
        {account.label}
      </span>
      <button
        onClick={() => handleToggleAccount(accountType, account.filePrefix, !account.hidden)}
        className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
          account.hidden ? "bg-cool-gray" : "bg-verde-claro"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            account.hidden ? "translate-x-0" : "translate-x-4"
          }`}
        />
      </button>
    </div>
  );

  return (
    <div>
      <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-1">Upload Cash Flow Data</h2>
      <p className="text-sm text-stone mb-4">
        Upload CSV exports, enter account balances, and run the pipeline.
      </p>

      <div className="flex items-center gap-2 mb-6">
        <label htmlFor="month-folder-select" className="text-sm font-medium text-warm-charcoal">Month:</label>
        <select
          id="month-folder-select"
          value={monthFolder}
          onChange={e => handleMonthChange(e.target.value)}
          className="border border-cool-gray rounded px-2 py-1 text-sm focus:outline-none focus:border-azul"
        >
          {monthOptions.map(m => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      {/* Manage Accounts */}
      <div className="mb-6">
        <button
          onClick={() => setShowManageAccounts(!showManageAccounts)}
          className="text-sm font-medium text-azul hover:text-verde-hoja flex items-center gap-1"
        >
          <svg className={`w-4 h-4 transition-transform ${showManageAccounts ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          Manage Accounts
        </button>
        {showManageAccounts && (
          <div className="mt-3 bg-cool-white rounded-lg p-4 border border-cool-gray">
            <p className="text-xs text-stone mb-3">
              Toggle accounts on/off. Hidden accounts will not appear in the upload form.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-semibold text-warm-charcoal mb-2">Credit Cards</h4>
                <div className="space-y-2">
                  {allCreditCards.map(a => renderAccountToggle(a, "credit_cards"))}
                </div>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-warm-charcoal mb-2">Checking & Savings</h4>
                <div className="space-y-2">
                  {allBankAccounts.map(a => renderAccountToggle(a, "bank_accounts"))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Credit Cards */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-warm-charcoal">Credit Cards</h3>
        {!showAddCC && (
          <button onClick={() => setShowAddCC(true)}
            className="text-xs text-azul hover:text-verde-hoja font-medium">+ Add Account</button>
        )}
      </div>
      {showAddCC && (
        <div className="flex items-center gap-2 mb-3 bg-cool-white rounded-lg px-3 py-2 border border-cool-gray">
          <input type="text" placeholder="Account name (e.g. Amex Gold)" value={newCCLabel}
            onChange={e => setNewCCLabel(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAddCC()}
            className="flex-1 text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul" autoFocus />
          <input type="text" placeholder="File prefix (optional)" value={newCCPrefix}
            onChange={e => setNewCCPrefix(e.target.value)}
            className="w-36 text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul" />
          <button onClick={handleAddCC} disabled={!newCCLabel.trim()}
            className="text-sm font-medium text-azul hover:text-verde-hoja disabled:opacity-40">Add</button>
          <button onClick={() => { setShowAddCC(false); setNewCCLabel(""); setNewCCPrefix(""); }}
            className="text-sm text-stone hover:text-coral">Cancel</button>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-8">
        {ccAccounts.map(({ label, filePrefix }) => (
          <div key={filePrefix} className="border border-cool-gray rounded-lg px-4 py-3">
            <label className="text-sm text-warm-charcoal font-medium block mb-2">{label}</label>
            <input type="file" accept=".csv" multiple
              onChange={e => {
                const newFiles = Array.from(e.target.files || []);
                if (newFiles.length === 0) return;
                setCcFiles(prev => {
                  const next = new Map(prev);
                  next.set(filePrefix, [...(next.get(filePrefix) || []), ...newFiles]);
                  return next;
                });
                e.target.value = "";
              }}
              className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray" />
            {(ccFiles.get(filePrefix) || []).length > 0 && (
              <ul className="mt-2 space-y-1">
                {(ccFiles.get(filePrefix) || []).map((f, i) => (
                  <li key={`${f.name}-${i}`} className="flex items-center justify-between text-xs text-stone bg-cool-white rounded px-2 py-1">
                    <span className="truncate">{f.name}</span>
                    <button
                      onClick={() => setCcFiles(prev => {
                        const next = new Map(prev);
                        const remaining = (next.get(filePrefix) || []).filter((_, idx) => idx !== i);
                        remaining.length > 0 ? next.set(filePrefix, remaining) : next.delete(filePrefix);
                        return next;
                      })}
                      className="text-coral hover:text-coral/70 ml-2 font-semibold">×</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      {/* Checking & Savings */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-warm-charcoal">Checking & Savings</h3>
        <div className="flex items-center gap-3">
          {!showAddBank && (
            <button onClick={() => setShowAddBank(true)}
              className="text-xs text-azul hover:text-verde-hoja font-medium">+ Add Account</button>
          )}
        </div>
      </div>
      {showAddBank && (
        <div className="flex items-center gap-2 mb-3 bg-cool-white rounded-lg px-3 py-2 border border-cool-gray">
          <input type="text" placeholder="Account name (e.g. Schwab Checking)" value={newBankLabel}
            onChange={e => setNewBankLabel(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAddBank()}
            className="flex-1 text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul" autoFocus />
          <input type="text" placeholder="File prefix (optional)" value={newBankPrefix}
            onChange={e => setNewBankPrefix(e.target.value)}
            className="w-36 text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul" />
          <button onClick={handleAddBank} disabled={!newBankLabel.trim()}
            className="text-sm font-medium text-azul hover:text-verde-hoja disabled:opacity-40">Add</button>
          <button onClick={() => { setShowAddBank(false); setNewBankLabel(""); setNewBankPrefix(""); }}
            className="text-sm text-stone hover:text-coral">Cancel</button>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-8">
        {bankAccounts.map(({ label, filePrefix }) => (
          <div key={filePrefix} className="border border-cool-gray rounded-lg px-4 py-3">
            <label className="text-sm text-warm-charcoal font-medium block mb-2">{label}</label>
            <input type="file" accept=".csv" multiple
              onChange={e => {
                const newFiles = Array.from(e.target.files || []);
                if (newFiles.length === 0) return;
                setBankFiles(prev => {
                  const next = new Map(prev);
                  next.set(filePrefix, [...(next.get(filePrefix) || []), ...newFiles]);
                  return next;
                });
                e.target.value = "";
              }}
              className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray mb-2" />
            {(bankFiles.get(filePrefix) || []).length > 0 && (
              <ul className="mb-2 space-y-1">
                {(bankFiles.get(filePrefix) || []).map((f, i) => (
                  <li key={`${f.name}-${i}`} className="flex items-center justify-between text-xs text-stone bg-cool-white rounded px-2 py-1">
                    <span className="truncate">{f.name}</span>
                    <button
                      onClick={() => setBankFiles(prev => {
                        const next = new Map(prev);
                        const remaining = (next.get(filePrefix) || []).filter((_, idx) => idx !== i);
                        remaining.length > 0 ? next.set(filePrefix, remaining) : next.delete(filePrefix);
                        return next;
                      })}
                      className="text-coral hover:text-coral/70 ml-2 font-semibold">×</button>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex items-center gap-2">
              <label className="text-xs text-stone">Current Balance:</label>
              <span className="text-xs text-stone">$</span>
              <input type="number" min="0" step="0.01" placeholder="0.00"
                value={balances[filePrefix] || ""}
                onChange={e => setBalances(prev => ({ ...prev, [filePrefix]: e.target.value }))}
                className="w-28 text-right text-sm px-2 py-1 rounded border border-cool-gray focus:outline-none focus:border-azul" />
            </div>
          </div>
        ))}
      </div>

      {/* Other files */}
      <h3 className="font-semibold text-warm-charcoal mb-3">Other Cash Flow Files</h3>
      <p className="text-xs text-stone mb-2">Upload additional CSVs with their original filenames.</p>
      <div className="flex items-center gap-4 mb-8">
        <input type="file" accept=".csv" multiple
          onChange={e => setOtherFiles(Array.from(e.target.files || []))}
          className="text-sm file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-cool-white file:text-stone hover:file:bg-cool-gray" />
        <label className="text-sm text-stone">Save to:</label>
        <select value={otherType} onChange={e => setOtherType(e.target.value as typeof otherType)}
          className="border border-stone rounded px-2 py-1 text-sm">
          <option>Credit Cards</option>
          <option>Checking and Savings</option>
        </select>
      </div>

      {/* Already saved files */}
      {savedFiles && (savedFiles["Credit Cards"].length > 0 || savedFiles["Checking and Savings"].length > 0) && (
        <div className="mb-8">
          <h3 className="font-semibold text-warm-charcoal mb-3">Already Saved This Month</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {(["Credit Cards", "Checking and Savings"] as const).map(subfolder => (
              <div key={subfolder}>
                <h4 className="text-sm font-semibold text-warm-charcoal mb-2">{subfolder}</h4>
                <div className="space-y-1">
                  {savedFiles[subfolder].length === 0 && (
                    <p className="text-xs text-stone">None yet</p>
                  )}
                  {savedFiles[subfolder].map(({ filename, date_range }) => (
                    <div key={filename} className="flex items-center justify-between text-sm bg-cool-white rounded px-3 py-1.5 border border-cool-gray">
                      <span className="truncate text-warm-charcoal">
                        {filename}
                        {date_range && (
                          <span className="text-xs text-stone ml-2">
                            ({date_range[0]} – {date_range[1]})
                          </span>
                        )}
                      </span>
                      <button
                        onClick={() => handleDeleteSavedFile(subfolder, filename)}
                        disabled={deletingFile === filename}
                        className="text-coral hover:text-coral/70 text-xs font-medium ml-2 disabled:opacity-40">
                        {deletingFile === filename ? "Deleting..." : "Remove"}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <hr className="border-cool-gray mb-6" />

      {/* Pipeline */}
      <h3 className="font-semibold text-warm-charcoal mb-3">Run Pipeline</h3>
      <div className="bg-cool-white rounded-lg px-4 py-3 mb-4 text-sm text-stone">
        Ready: <span className="font-semibold text-warm-charcoal">{totalFiles}</span> cash flow file(s)
        {hasBalances && <span className="ml-2">+ account balances ({balanceDate})</span>}
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

      <button onClick={handleSubmit}
        disabled={(totalFiles === 0 && !hasBalances) || isRunning}
        className="bg-azul text-white px-6 py-2.5 rounded font-semibold text-sm hover:bg-verde-claro disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        {isRunning ? "Running..." : "Save Files & Run"}
      </button>

      <PipelineRunner results={results} savedCount={savedCount} isRunning={isRunning} />
      {balancesSaved && (
        <div className="bg-verde-claro/10 border border-verde-claro rounded-lg px-4 py-2 text-sm text-verde-hoja mt-3">
          Account balances saved for {balanceDate}
        </div>
      )}
    </div>
  );
}
