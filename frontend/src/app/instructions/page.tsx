"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const PROD_ACCOUNTS = [
  { name: "Aeroplan", type: "Chase Credit Card", owner: "Maria", format: "Chase card CSV", notes: "Export from Chase → Download activity" },
  { name: "AmazonPrime", type: "Chase Credit Card", owner: "Maria", format: "Chase card CSV", notes: "Export from Chase → Download activity" },
  { name: "United", type: "Chase Credit Card", owner: "Maria", format: "Chase card CSV", notes: "Export from Chase → Download activity" },
  { name: "VentureX", type: "Capital One Credit Card", owner: "Maria", format: "Capital One CSV (Debit/Credit columns)", notes: "Export from Capital One → Download transactions" },
  { name: "VentureOne", type: "Capital One Credit Card", owner: "Scott", format: "Capital One CSV (Debit/Credit columns)", notes: "Export from Capital One → Download transactions" },
  { name: "Alaska", type: "BoA Credit Card", owner: "Maria", format: "BoA card CSV (Posted Date, Payee, Amount)", notes: "Export from Bank of America → Download transactions" },
  { name: "CashRewards-Scott", type: "BoA Credit Card", owner: "Scott", format: "BoA card CSV (Posted Date, Payee, Amount)", notes: "Files named with _2382 suffix" },
  { name: "Alaska-Scott", type: "BoA Credit Card", owner: "Scott", format: "BoA card CSV (Posted Date, Payee, Amount)", notes: "Files named with _3728 suffix" },
  { name: "CitiAAdvantage", type: "Citi Credit Card", owner: "Scott", format: "Citi CSV (Status, Date, Description, Debit, Credit)", notes: "Export from Citi → Download transactions" },
  { name: "Barclays", type: "Barclays Credit Card", owner: "Scott", format: "Barclays CSV (has header section before data)", notes: "Export from Barclays → Download activity" },
  { name: "SoFi-JointChecking", type: "Checking", owner: "Joint", format: "SoFi CSV (Date, Description, Amount)", notes: "Export from SoFi → Download transactions" },
  { name: "SoFi-JointSavings", type: "Savings", owner: "Joint", format: "SoFi CSV (Date, Description, Amount)", notes: "Export from SoFi → Download transactions" },
  { name: "BoA-Checking", type: "Checking", owner: "Joint", format: "BoA bank CSV (has summary header)", notes: "Export from Bank of America → Download transactions" },
  { name: "BoA-Savings", type: "Savings", owner: "Joint", format: "BoA bank CSV (has summary header)", notes: "Export from Bank of America → Download transactions" },
  { name: "Chase-Checking", type: "Checking", owner: "Joint", format: "Chase checking CSV (82-column format)", notes: "Export from Chase → Download activity" },
];

const DEMO_ACCOUNTS = [
  { name: "Rewards Card", type: "Credit Card", owner: "Viviana", format: "Standard CSV", notes: "Primary spending card" },
  { name: "Travel Card", type: "Credit Card", owner: "Michael", format: "Standard CSV", notes: "Travel rewards card" },
  { name: "Joint Checking", type: "Checking", owner: "Joint", format: "Standard CSV", notes: "Main checking account" },
  { name: "Joint Savings", type: "Savings", owner: "Joint", format: "Standard CSV", notes: "Savings account" },
];

export default function InstructionsPage() {
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });
  const familyName = config?.family_name || "Woffieta Family";
  const isDemo = config?.is_demo ?? false;
  const accounts = isDemo ? DEMO_ACCOUNTS : PROD_ACCOUNTS;

  return (
    <div>
      {/* Header */}
      <div className="pb-2 mb-6 border-b-[3px]"
        style={{ borderImage: "linear-gradient(90deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1" }}>
        <h1 className="font-[Cormorant_Garamond,serif] text-[2.4rem] font-normal text-warm-charcoal leading-tight">
          {familyName}
        </h1>
        <p className="text-[0.85rem] font-light text-stone tracking-[0.1em] uppercase">
          Instructions
        </p>
      </div>

      {/* Monthly Update Workflow */}
      <section className="mb-10">
        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Monthly Update Workflow</h2>
        <div className="bg-cool-white rounded-lg border border-cool-gray p-6 space-y-4">
          <div className="flex gap-3">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-azul text-white text-sm font-bold flex items-center justify-center">1</span>
            <div>
              <p className="font-semibold text-warm-charcoal">Export CSV files from each account</p>
              <p className="text-sm text-stone mt-1">Log into each bank/card website and download transaction CSVs for the current month. See the Accounts table below for details on each account.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-azul text-white text-sm font-bold flex items-center justify-center">2</span>
            <div>
              <p className="font-semibold text-warm-charcoal">Upload files via the Cash Flow &rarr; Add Data tab</p>
              <p className="text-sm text-stone mt-1">Assign each CSV to its corresponding account slot (credit card or checking/savings). Enter current account balances if desired. The app will automatically name files with the correct prefix.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-azul text-white text-sm font-bold flex items-center justify-center">3</span>
            <div>
              <p className="font-semibold text-warm-charcoal">Run the pipeline</p>
              <p className="text-sm text-stone mt-1">Check &ldquo;Run Cash Flow pipeline&rdquo; and optionally &ldquo;Generate Excel report&rdquo;, then click &ldquo;Save Files &amp; Run&rdquo;. The pipeline reads all CSVs, classifies transactions, and generates monthly reports.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-azul text-white text-sm font-bold flex items-center justify-center">4</span>
            <div>
              <p className="font-semibold text-warm-charcoal">Review the dashboard</p>
              <p className="text-sm text-stone mt-1">Check the Cash Flow dashboard for the updated numbers. Use the category drill-down to verify classifications. Review &ldquo;Unclassified&rdquo; transactions and create action items for anything that needs investigation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Accounts Table */}
      <section className="mb-10">
        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Accounts on File</h2>
        <div className="overflow-x-auto rounded-lg border border-cool-gray">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-cool-white">
                <th className="text-left px-4 py-3 font-semibold text-stone">Account</th>
                <th className="text-left px-4 py-3 font-semibold text-stone">Type</th>
                <th className="text-left px-4 py-3 font-semibold text-stone">Owner</th>
                <th className="text-left px-4 py-3 font-semibold text-stone">CSV Format</th>
                <th className="text-left px-4 py-3 font-semibold text-stone">Notes</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map(a => (
                <tr key={a.name} className="border-t border-cool-gray hover:bg-cool-white/50">
                  <td className="px-4 py-2.5 font-medium">{a.name}</td>
                  <td className="px-4 py-2.5 text-stone">{a.type}</td>
                  <td className="px-4 py-2.5 text-stone">{a.owner}</td>
                  <td className="px-4 py-2.5 text-stone">{a.format}</td>
                  <td className="px-4 py-2.5 text-stone">{a.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* What the Pipeline Produces */}
      <section className="mb-10">
        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Pipeline Outputs</h2>
        <div className="bg-cool-white rounded-lg border border-cool-gray p-6 space-y-3 text-sm">
          <div>
            <p className="font-semibold text-warm-charcoal">all_transactions.csv</p>
            <p className="text-stone">Master file with every transaction, classified by flow type (spending, income, cc_payment, internal_transfer), category, and subcategory.</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">Monthly/{'{year}'}/{'{Month}_{year}'}.csv</p>
            <p className="text-stone">Per-month transaction files for easy review. Same format as all_transactions.csv.</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">CashFlow_Report.xlsx</p>
            <p className="text-stone">Excel report with summary sheets, charts, and pivot tables (generated if &ldquo;Generate Excel report&rdquo; is checked).</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">transaction_notes.json</p>
            <p className="text-stone">Notes added to individual transactions (e.g., &ldquo;Reimbursable&rdquo;, trip names). Persists across pipeline reruns.</p>
          </div>
        </div>
      </section>

      {/* Key Concepts */}
      <section className="mb-10">
        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Key Concepts</h2>
        <div className="bg-cool-white rounded-lg border border-cool-gray p-6 space-y-3 text-sm">
          <div>
            <p className="font-semibold text-warm-charcoal">Flow Types</p>
            <p className="text-stone"><strong>spending</strong> &mdash; purchases and expenses (included in outflows). <strong>income</strong> &mdash; paychecks, reimbursements, rewards (included in inflows). <strong>cc_payment</strong> &mdash; credit card bill payments (excluded to avoid double-counting). <strong>internal_transfer</strong> &mdash; money moving between your own accounts (excluded). <strong>other</strong> &mdash; refunds, credits, misc (reviewed individually).</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">Post Date vs Transaction Date</p>
            <p className="text-stone">The app uses <strong>post date</strong> for monthly attribution. A transaction made on Jan 31 that posts Feb 1 will appear in February.</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">Spillover Transactions</p>
            <p className="text-stone">When a CSV export contains transactions that posted in the following month (e.g., a Feb export with Mar 1 transactions), those are excluded until that month&rsquo;s data is uploaded. This prevents incomplete months from appearing in the dashboard.</p>
          </div>
          <div>
            <p className="font-semibold text-warm-charcoal">Transaction Notes</p>
            <p className="text-stone">Notes can be added to individual transactions via the API. Notes persist in transaction_notes.json and are merged into CSVs when the pipeline runs. Useful for marking reimbursable expenses, trip names, or other context.</p>
          </div>
        </div>
      </section>

      {/* Folder Structure */}
      <section className="mb-10">
        <h2 className="font-[Lora,serif] text-xl text-warm-charcoal mb-4">Data Folder Structure</h2>
        <div className="bg-cool-white rounded-lg border border-cool-gray p-6 text-sm font-mono text-warm-charcoal">
          <pre className="whitespace-pre-wrap">{`${isDemo ? "Demo" : "Production"}/CashFlow/
├── 2025/                          # Annual exports (full year data)
│   ├── Credit Cards/              # Card transaction CSVs
│   └── Checking and Savings/      # Bank account CSVs
├── Jan26/                         # Monthly uploads
│   ├── Credit Cards/
│   └── Checking and Savings/
├── Feb26/
├── Monthly/                       # AUTO-GENERATED per-month files
│   ├── 2025/
│   └── 2026/
├── all_transactions.csv           # AUTO-GENERATED master file
└── CashFlow_Report.xlsx           # AUTO-GENERATED Excel report`}</pre>
        </div>
      </section>
    </div>
  );
}
