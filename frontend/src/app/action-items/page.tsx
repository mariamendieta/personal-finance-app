"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ActionItem } from "@/lib/api";

const STATUS_OPTIONS = ["In Progress", "Open", "Done"];
const CATEGORY_OPTIONS = ["Cash Flow", "Investment", "Other"];

const STATUS_BADGE: Record<string, string> = {
  "In Progress": "bg-marigold/15 text-marigold border-marigold",
  "Open": "bg-azul/10 text-azul border-azul",
  "Done": "bg-verde-claro/15 text-verde-hoja border-verde-hoja",
};

export default function ActionItemsPage() {
  const queryClient = useQueryClient();
  const { data: items, isLoading } = useQuery({
    queryKey: ["action-items"],
    queryFn: api.getActionItems,
  });
  const { data: config } = useQuery({
    queryKey: ["config"],
    queryFn: api.getConfig,
  });

  // Filters
  const [filterStatus, setFilterStatus] = useState("All");
  const [filterAssignee, setFilterAssignee] = useState("All");
  const [filterCategory, setFilterCategory] = useState("All");
  const [filterMonth, setFilterMonth] = useState("All");

  // Add form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTask, setNewTask] = useState("");
  const [newAssignee, setNewAssignee] = useState("Maria");
  const [newCategory, setNewCategory] = useState("Other");

  const updateStatus = useMutation({
    mutationFn: ({ task, status }: { task: string; status: string }) => {
      const dateCompleted = status === "Done" ? new Date().toISOString().split("T")[0] : "";
      return api.updateActionItemStatus(task, status, dateCompleted);
    },
    onSuccess: (data) => queryClient.setQueryData(["action-items"], data),
  });

  const addItem = useMutation({
    mutationFn: () => {
      const today = new Date().toISOString().split("T")[0];
      return api.addActionItem(newTask, newAssignee, newCategory, today);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["action-items"], data);
      setNewTask("");
      setShowAddForm(false);
    },
  });

  const deleteItem = useMutation({
    mutationFn: (task: string) => api.deleteActionItem(task),
    onSuccess: (data) => queryClient.setQueryData(["action-items"], data),
  });

  // Derived filter options
  const assignees = useMemo(() => {
    if (!items) return [];
    return [...new Set(items.map(i => i.assignee))].sort();
  }, [items]);

  const months = useMemo(() => {
    if (!items) return [];
    const set = new Set(items.map(i => {
      const d = new Date(i.date_created);
      return `${d.toLocaleString("en-US", { month: "short" })} ${d.getFullYear()}`;
    }));
    return [...set].sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
  }, [items]);

  const filtered = useMemo(() => {
    if (!items) return [];
    return items.filter(i => {
      if (filterStatus !== "All" && i.status !== filterStatus) return false;
      if (filterAssignee !== "All" && i.assignee !== filterAssignee) return false;
      if (filterCategory !== "All" && i.category !== filterCategory) return false;
      if (filterMonth !== "All") {
        const d = new Date(i.date_created);
        const label = `${d.toLocaleString("en-US", { month: "short" })} ${d.getFullYear()}`;
        if (label !== filterMonth) return false;
      }
      return true;
    });
  }, [items, filterStatus, filterAssignee, filterCategory, filterMonth]);

  const inProgress = filtered.filter(i => i.status === "In Progress");
  const open = filtered.filter(i => i.status === "Open");
  const done = filtered.filter(i => i.status === "Done");

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
          Action Items
        </p>
      </div>

      {/* Filters + Add */}
      <div className="flex items-end gap-4 mb-6 flex-wrap">
        <div>
          <label className="block text-xs font-semibold text-stone uppercase tracking-wide mb-1">Status</label>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="border border-cool-gray rounded px-3 py-1.5 text-sm text-warm-charcoal">
            <option>All</option>
            {STATUS_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-stone uppercase tracking-wide mb-1">Assignee</label>
          <select value={filterAssignee} onChange={e => setFilterAssignee(e.target.value)}
            className="border border-cool-gray rounded px-3 py-1.5 text-sm text-warm-charcoal">
            <option>All</option>
            {assignees.map(a => <option key={a}>{a}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-stone uppercase tracking-wide mb-1">Category</label>
          <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)}
            className="border border-cool-gray rounded px-3 py-1.5 text-sm text-warm-charcoal">
            <option>All</option>
            {CATEGORY_OPTIONS.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-stone uppercase tracking-wide mb-1">Date Created</label>
          <select value={filterMonth} onChange={e => setFilterMonth(e.target.value)}
            className="border border-cool-gray rounded px-3 py-1.5 text-sm text-warm-charcoal">
            <option>All</option>
            {months.map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="ml-auto">
          {!showAddForm && (
            <button onClick={() => setShowAddForm(true)}
              className="bg-azul text-white px-4 py-1.5 rounded font-semibold text-sm hover:bg-verde-claro transition-colors">
              + Add Action Item
            </button>
          )}
        </div>
      </div>

      {/* Add form */}
      {showAddForm && (
        <div className="bg-cool-white rounded-lg p-4 border border-cool-gray max-w-3xl mb-6">
          <div className="flex gap-3 mb-3">
            <input type="text" value={newTask} onChange={e => setNewTask(e.target.value)}
              placeholder="Describe the action item..."
              className="flex-1 text-sm px-3 py-2 rounded border border-cool-gray focus:outline-none focus:border-azul"
              autoFocus
              onKeyDown={e => e.key === "Enter" && newTask.trim() && addItem.mutate()} />
            <select value={newAssignee} onChange={e => setNewAssignee(e.target.value)}
              className="text-sm px-3 py-2 rounded border border-cool-gray">
              <option>Maria</option>
              <option>Scott</option>
            </select>
            <select value={newCategory} onChange={e => setNewCategory(e.target.value)}
              className="text-sm px-3 py-2 rounded border border-cool-gray">
              {CATEGORY_OPTIONS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={() => addItem.mutate()} disabled={!newTask.trim()}
              className="bg-azul text-white px-4 py-1.5 rounded text-sm font-medium hover:bg-verde-claro disabled:opacity-40 transition-colors">
              Add
            </button>
            <button onClick={() => { setShowAddForm(false); setNewTask(""); }}
              className="text-stone px-4 py-1.5 rounded text-sm hover:bg-cool-gray transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <p className="text-stone">Loading action items...</p>
      ) : (
        <div className="space-y-8">
          {inProgress.length > 0 && (
            <StatusTable title="In Progress" items={inProgress} count={inProgress.length}
              onStatusChange={(task, status) => updateStatus.mutate({ task, status })}
              onDelete={task => deleteItem.mutate(task)} />
          )}
          {open.length > 0 && (
            <StatusTable title="Open" items={open} count={open.length}
              onStatusChange={(task, status) => updateStatus.mutate({ task, status })}
              onDelete={task => deleteItem.mutate(task)} />
          )}
          {done.length > 0 && (
            <StatusTable title="Done" items={done} count={done.length}
              onStatusChange={(task, status) => updateStatus.mutate({ task, status })}
              onDelete={task => deleteItem.mutate(task)}
              defaultCollapsed />
          )}
          {filtered.length === 0 && (
            <p className="text-stone text-center py-12">
              {items?.length === 0 ? "No action items yet. Add one above!" : "No items match the current filters."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

type SortField = "task" | "assignee" | "category" | "date_created" | "date_completed";
type SortDir = "asc" | "desc";

function SortHeader({
  label,
  field,
  activeField,
  direction,
  onSort,
  className = "",
}: {
  label: string;
  field: SortField;
  activeField: SortField | null;
  direction: SortDir;
  onSort: (field: SortField) => void;
  className?: string;
}) {
  const isActive = activeField === field;
  return (
    <th
      className={`text-left px-4 py-3 font-semibold text-stone cursor-pointer select-none hover:text-azul transition-colors ${className}`}
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <span className={`text-[10px] ${isActive ? "text-azul" : "text-mid-gray"}`}>
          {isActive ? (direction === "asc" ? "▲" : "▼") : "⇅"}
        </span>
      </span>
    </th>
  );
}

function sortItems(items: ActionItem[], field: SortField | null, dir: SortDir): ActionItem[] {
  if (!field) return items;
  return [...items].sort((a, b) => {
    const va = a[field] || "";
    const vb = b[field] || "";
    const cmp = va.localeCompare(vb);
    return dir === "asc" ? cmp : -cmp;
  });
}

function StatusTable({
  title,
  items,
  count,
  onStatusChange,
  onDelete,
  defaultCollapsed = false,
}: {
  title: string;
  items: ActionItem[];
  count: number;
  onStatusChange: (task: string, status: string) => void;
  onDelete: (task: string) => void;
  defaultCollapsed?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(!defaultCollapsed);
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const badgeClass = STATUS_BADGE[title] || "";

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const sorted = sortItems(items, sortField, sortDir);

  return (
    <div>
      <button onClick={() => setIsOpen(!isOpen)} className="flex items-center gap-2 mb-3">
        <span className="text-xs text-stone">{isOpen ? "▼" : "▶"}</span>
        <h2 className="font-[Lora,serif] text-lg text-warm-charcoal">{title}</h2>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${badgeClass}`}>{count}</span>
      </button>

      {isOpen && (
        <div className="overflow-x-auto rounded-lg border border-cool-gray">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-cool-white">
                <SortHeader label="Task" field="task" activeField={sortField} direction={sortDir} onSort={handleSort} />
                <SortHeader label="Assignee" field="assignee" activeField={sortField} direction={sortDir} onSort={handleSort} className="w-28" />
                <SortHeader label="Category" field="category" activeField={sortField} direction={sortDir} onSort={handleSort} className="w-28" />
                <th className="text-left px-4 py-3 font-semibold text-stone w-32">Status</th>
                <SortHeader label="Date Created" field="date_created" activeField={sortField} direction={sortDir} onSort={handleSort} className="w-32" />
                <SortHeader label="Date Completed" field="date_completed" activeField={sortField} direction={sortDir} onSort={handleSort} className="w-36" />
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(item => (
                <tr key={item.task} className="border-t border-cool-gray hover:bg-cool-white/50 group">
                  <td className={`px-4 py-2.5 ${item.status === "Done" ? "line-through text-stone" : "text-warm-charcoal"}`}>
                    {item.task}
                  </td>
                  <td className="px-4 py-2.5 text-stone">{item.assignee}</td>
                  <td className="px-4 py-2.5 text-stone">{item.category}</td>
                  <td className="px-4 py-2.5">
                    <select value={item.status} onChange={e => onStatusChange(item.task, e.target.value)}
                      className={`text-xs font-medium px-2 py-1 rounded border ${STATUS_BADGE[item.status] || ""}`}>
                      {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-2.5 text-stone">{item.date_created}</td>
                  <td className="px-4 py-2.5 text-stone">{item.date_completed || "—"}</td>
                  <td className="px-2 py-2.5">
                    <button onClick={() => onDelete(item.task)}
                      className="text-mid-gray hover:text-coral opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Delete">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
