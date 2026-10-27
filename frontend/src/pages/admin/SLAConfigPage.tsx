import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "@/hooks/use-toast";
import type { SLARule, Bureau } from "@/types";
import { formatDate } from "@/lib/utils";
import { Plus, Edit, Trash2, Info } from "lucide-react";

// ── SLA form modal ────────────────────────────────────────────────────────────

interface SLAFormState {
  name: string;
  bureau_id: string;
  category: string;
  priority: string;
  days_to_resolve: number;
  warning_days_before: number;
  is_active: boolean;
}

const CATEGORIES = [
  "Fee Refund", "Faculty Issues", "Infrastructure", "Examination",
  "Affiliation", "Accreditation", "Admissions", "Conduct/Discipline",
  "Salary Dispute", "Other",
];

const PRIORITIES = ["low", "medium", "high", "critical"];

function SLAModal({
  open,
  onClose,
  rule,
  bureaus,
}: {
  open: boolean;
  onClose: () => void;
  rule?: SLARule | null;
  bureaus: Bureau[];
}) {
  const queryClient = useQueryClient();
  const isEdit = !!rule;

  const [form, setForm] = useState<SLAFormState>({
    name: rule?.name ?? "",
    bureau_id: rule?.bureau?.id ?? "",
    category: rule?.category ?? "",
    priority: rule?.priority ?? "",
    days_to_resolve: rule?.days_to_resolve ?? 30,
    warning_days_before: rule?.warning_days_before ?? 5,
    is_active: rule?.is_active ?? true,
  });

  const set = <K extends keyof SLAFormState>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value =
        e.target.type === "checkbox"
          ? (e.target as HTMLInputElement).checked
          : e.target.type === "number"
          ? Number(e.target.value)
          : e.target.value;
      setForm((f) => ({ ...f, [key]: value }));
    };

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name,
        bureau_id: form.bureau_id || null,
        category: form.category || null,
        priority: form.priority || null,
        days_to_resolve: form.days_to_resolve,
        warning_days_before: form.warning_days_before,
        is_active: form.is_active,
      };
      if (isEdit) {
        const r = await apiClient.patch(`/sla-rules/${rule!.id}`, payload);
        return r.data;
      } else {
        const r = await apiClient.post("/sla-rules", payload);
        return r.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sla-rules"] });
      toast({ title: isEdit ? "SLA rule updated" : "SLA rule created" });
      onClose();
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit SLA Rule" : "Create SLA Rule"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm">
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
            <Info className="inline h-3 w-3 mr-1" />
            Demo configuration — update with official AICTE SLA policies before production use.
          </div>

          <div>
            <label className="font-medium text-gray-700 block mb-1">Rule Name *</label>
            <Input value={form.name} onChange={set("name")} placeholder="e.g. PGRC Fee Refund High Priority" required />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-medium text-gray-700 block mb-1">Bureau</label>
              <select
                value={form.bureau_id}
                onChange={set("bureau_id")}
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Bureaus</option>
                {bureaus.map((b) => (
                  <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-medium text-gray-700 block mb-1">Category</label>
              <select
                value={form.category}
                onChange={set("category")}
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-medium text-gray-700 block mb-1">Priority</label>
              <select
                value={form.priority}
                onChange={set("priority")}
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Priorities</option>
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-medium text-gray-700 block mb-1">Status</label>
              <select
                value={form.is_active ? "true" : "false"}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.value === "true" }))}
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-medium text-gray-700 block mb-1">Days to Resolve *</label>
              <Input type="number" min={1} value={form.days_to_resolve} onChange={set("days_to_resolve")} />
            </div>
            <div>
              <label className="font-medium text-gray-700 block mb-1">Warning Days Before *</label>
              <Input type="number" min={0} value={form.warning_days_before} onChange={set("warning_days_before")} />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => mutation.mutate()} disabled={!form.name.trim() || mutation.isPending} isLoading={mutation.isPending}>
            {isEdit ? "Update" : "Create"} Rule
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function SLAConfigPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editRule, setEditRule] = useState<SLARule | null>(null);
  const [deleteRule, setDeleteRule] = useState<SLARule | null>(null);

  const { data: rules, isLoading } = useQuery({
    queryKey: ["sla-rules"],
    queryFn: async () => {
      const r = await apiClient.get<SLARule[]>("/sla-rules");
      return r.data;
    },
  });

  const { data: bureaus = [] } = useQuery({
    queryKey: ["bureaus"],
    queryFn: async () => {
      const r = await apiClient.get<Bureau[]>("/bureaus");
      return r.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/sla-rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sla-rules"] });
      toast({ title: "SLA rule deleted" });
      setDeleteRule(null);
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const columns: ColumnDef<SLARule>[] = [
    {
      key: "name",
      header: "Rule Name",
      cell: (row) => <span className="font-medium">{row.name}</span>,
    },
    {
      key: "bureau",
      header: "Bureau",
      cell: (row) => row.bureau?.code ?? <span className="text-gray-400">All Bureaus</span>,
    },
    {
      key: "category",
      header: "Category",
      cell: (row) => row.category ?? <span className="text-gray-400">All</span>,
    },
    {
      key: "priority",
      header: "Priority",
      cell: (row) =>
        row.priority ? (
          <Badge variant="secondary" className="capitalize">
            {row.priority}
          </Badge>
        ) : (
          <span className="text-gray-400">All</span>
        ),
    },
    {
      key: "days_to_resolve",
      header: "Resolution Days",
      cell: (row) => (
        <span className="font-semibold text-indigo-700">{row.days_to_resolve} days</span>
      ),
    },
    {
      key: "warning_days_before",
      header: "Warning At",
      cell: (row) => `${row.warning_days_before} days before`,
    },
    {
      key: "is_active",
      header: "Status",
      cell: (row) => (
        <Badge variant={row.is_active ? "success" : "secondary"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      key: "updated_at",
      header: "Last Updated",
      cell: (row) => formatDate(row.updated_at),
    },
    {
      key: "actions",
      header: "",
      cell: (row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={() => setEditRule(row)}>
            <Edit className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-red-600 hover:text-red-700"
            onClick={() => setDeleteRule(row)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="SLA Configuration"
        subtitle="Service level agreement rules and deadline settings"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Administration" },
          { label: "SLA Settings" },
        ]}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add SLA Rule
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800 flex items-start gap-2">
          <Info className="h-4 w-4 shrink-0 mt-0.5" />
          <span>
            <strong>Demo configuration</strong> — SLA values shown are demonstration defaults.
            These must be replaced with actual AICTE policy values before production use.
          </span>
        </div>

        <DataTable
          columns={columns}
          data={rules ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No SLA rules configured. Add your first rule."
        />
      </div>

      <SLAModal open={createOpen} onClose={() => setCreateOpen(false)} bureaus={bureaus} />
      <SLAModal open={!!editRule} onClose={() => setEditRule(null)} rule={editRule} bureaus={bureaus} />

      <AlertDialog open={!!deleteRule} onOpenChange={() => setDeleteRule(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete SLA Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Delete rule <strong>{deleteRule?.name}</strong>? This will not affect existing cases
              that already have their SLA deadline calculated.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => deleteRule && deleteMutation.mutate(deleteRule.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
