import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DataTable, type ColumnDef } from "@/components/shared/DataTable";
import { SearchInput } from "@/components/shared/SearchInput";
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
import type { User, PaginatedResponse } from "@/types";
import { formatDate } from "@/lib/utils";
import { Plus, Edit, KeyRound, UserCheck, UserX } from "lucide-react";

// ── User form ──────────────────────────────────────────────────────────────────

interface UserFormData {
  email: string;
  full_name: string;
  password: string;
  role_name: string;
  bureau_id: string;
  region_id: string;
}

const ROLE_OPTIONS = [
  "system_administrator", "rb_officer", "pgrc_officer",
  "bureau_officer", "regional_officer", "senior_management",
];

function UserFormModal({
  open,
  onClose,
  editUser,
}: {
  open: boolean;
  onClose: () => void;
  editUser?: User | null;
}) {
  const queryClient = useQueryClient();
  const isEdit = !!editUser;

  const [formData, setFormData] = useState<UserFormData>({
    email: editUser?.email ?? "",
    full_name: editUser?.full_name ?? "",
    password: "",
    role_name: (editUser?.role as string) ?? "",
    bureau_id: editUser?.bureau?.id ?? "",
    region_id: editUser?.region?.id ?? "",
  });

  const mutation = useMutation({
    mutationFn: async (data: Partial<UserFormData>) => {
      if (isEdit) {
        const response = await apiClient.patch(`/users/${editUser!.id}`, data);
        return response.data;
      } else {
        const response = await apiClient.post("/users", data);
        return response.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast({ title: isEdit ? "User updated" : "User created" });
      onClose();
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: Partial<UserFormData> = {
      email: formData.email,
      full_name: formData.full_name,
      role_name: formData.role_name,
      bureau_id: formData.bureau_id || undefined,
      region_id: formData.region_id || undefined,
    };
    if (!isEdit && formData.password) payload.password = formData.password;
    mutation.mutate(payload);
  };

  const set = (key: keyof UserFormData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFormData((f) => ({ ...f, [key]: e.target.value }));

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit User" : "Create User"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Full Name *</label>
              <Input value={formData.full_name} onChange={set("full_name")} placeholder="Full name" required />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Email *</label>
              <Input type="email" value={formData.email} onChange={set("email")} placeholder="email@example.com" required />
            </div>
          </div>

          {!isEdit && (
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Password *</label>
              <Input type="password" value={formData.password} onChange={set("password")} placeholder="Minimum 8 characters" required />
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Role *</label>
            <select
              value={formData.role_name}
              onChange={set("role_name")}
              required
              className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select role...</option>
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {r.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Bureau ID</label>
              <Input value={formData.bureau_id} onChange={set("bureau_id")} placeholder="Bureau UUID (optional)" />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Region ID</label>
              <Input value={formData.region_id} onChange={set("region_id")} placeholder="Region UUID (optional)" />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" isLoading={mutation.isPending}>
              {isEdit ? "Update User" : "Create User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function UserManagementPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [resetUser, setResetUser] = useState<User | null>(null);
  const [toggleUser, setToggleUser] = useState<User | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users", { search, page }],
    queryFn: async () => {
      // /users returns an array or a paginated response — normalise to paginated shape
      const response = await apiClient.get<User[] | PaginatedResponse<User>>("/users/", {
        params: { search: search || undefined, page, size: 20 },
      });
      const raw = response.data;
      if (Array.isArray(raw)) {
        return { items: raw, total: raw.length, page: 1, page_size: raw.length, pages: 1 } as PaginatedResponse<User>;
      }
      return raw as PaginatedResponse<User>;
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: async (user: User) => {
      const response = await apiClient.patch(`/users/${user.id}`, {
        is_active: !user.is_active,
      });
      return response.data;
    },
    onSuccess: (_, user) => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast({ title: user.is_active ? "User deactivated" : "User activated" });
      setToggleUser(null);
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const resetPasswordMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await apiClient.post(`/users/${userId}/reset-password`);
      return response.data;
    },
    onSuccess: () => {
      toast({ title: "Password reset link sent to user's email" });
      setResetUser(null);
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  const columns: ColumnDef<User>[] = [
    {
      key: "full_name",
      header: "Name",
      cell: (row) => (
        <div>
          <p className="font-medium text-gray-900">{row.full_name}</p>
          <p className="text-xs text-gray-400">{row.email}</p>
        </div>
      ),
    },
    {
      key: "role",
      header: "Role",
      cell: (row) => (
        <Badge variant="secondary" className="capitalize">
          {(row.role as string).replace(/_/g, " ")}
        </Badge>
      ),
    },
    {
      key: "bureau",
      header: "Bureau",
      cell: (row) => row.bureau?.code ?? "—",
    },
    {
      key: "region",
      header: "Region",
      cell: (row) => row.region?.name ?? "—",
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
      key: "last_login",
      header: "Last Login",
      cell: (row) => formatDate(row.last_login),
    },
    {
      key: "last_login",
      header: "Last Login",
      sortable: false,
      cell: (row) => formatDate(row.last_login ?? ""),
    },
    {
      key: "actions",
      header: "",
      cell: (row) => (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setEditUser(row)}
            title="Edit user"
          >
            <Edit className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setToggleUser(row)}
            title={row.is_active ? "Deactivate" : "Activate"}
          >
            {row.is_active ? (
              <UserX className="h-3.5 w-3.5 text-red-500" />
            ) : (
              <UserCheck className="h-3.5 w-3.5 text-green-600" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setResetUser(row)}
            title="Reset password"
          >
            <KeyRound className="h-3.5 w-3.5 text-amber-500" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="User Management"
        subtitle="Manage system users, roles, and access permissions"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Administration" },
          { label: "Users" },
        ]}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create User
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <SearchInput
          value={search}
          onChange={(val) => { setSearch(val); setPage(1); }}
          placeholder="Search by name or email..."
          className="max-w-sm"
        />

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          rowKey={(row) => row.id}
          emptyMessage="No users found."
          pagination={
            data
              ? { page: data.page, size: data.page_size, total: data.total, pages: data.pages }
              : undefined
          }
          onPageChange={setPage}
        />
      </div>

      {/* Create user modal */}
      <UserFormModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />

      {/* Edit user modal */}
      <UserFormModal
        open={!!editUser}
        onClose={() => setEditUser(null)}
        editUser={editUser}
      />

      {/* Toggle active confirmation */}
      <AlertDialog open={!!toggleUser} onOpenChange={() => setToggleUser(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {toggleUser?.is_active ? "Deactivate" : "Activate"} User
            </AlertDialogTitle>
            <AlertDialogDescription>
              {toggleUser?.is_active
                ? `Deactivate ${toggleUser?.full_name}? They will no longer be able to log in.`
                : `Activate ${toggleUser?.full_name}? They will regain access to the system.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => toggleUser && toggleActiveMutation.mutate(toggleUser)}
            >
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset password confirmation */}
      <AlertDialog open={!!resetUser} onOpenChange={() => setResetUser(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset Password</AlertDialogTitle>
            <AlertDialogDescription>
              Send a password reset to {resetUser?.full_name} ({resetUser?.email})?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => resetUser && resetPasswordMutation.mutate(resetUser.id)}
            >
              Send Reset
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
