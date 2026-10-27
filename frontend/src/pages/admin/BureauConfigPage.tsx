import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import type { Bureau, Region } from "@/types";
import { Building2, MapPin, Plus, Edit, Trash2 } from "lucide-react";

// ── Bureau Form Modal ─────────────────────────────────────────────────────────

function BureauModal({
  open,
  onClose,
  bureau,
}: {
  open: boolean;
  onClose: () => void;
  bureau?: Bureau | null;
}) {
  const queryClient = useQueryClient();
  const isEdit = !!bureau;
  const [name, setName] = useState(bureau?.name ?? "");
  const [code, setCode] = useState(bureau?.code ?? "");
  const [description, setDescription] = useState(bureau?.description ?? "");

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = { name, code, description };
      if (isEdit) {
        const r = await apiClient.patch(`/bureaus/${bureau!.id}`, payload);
        return r.data;
      } else {
        const r = await apiClient.post("/bureaus", payload);
        return r.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bureaus"] });
      toast({ title: isEdit ? "Bureau updated" : "Bureau created" });
      onClose();
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Bureau" : "Create Bureau"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Bureau Code *</label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. RB, PGRC" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Bureau Name *</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full bureau name" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Description</label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Brief description..." rows={2} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => mutation.mutate()} disabled={!name.trim() || !code.trim() || mutation.isPending} isLoading={mutation.isPending}>
            {isEdit ? "Update" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Region Form Modal ─────────────────────────────────────────────────────────

function RegionModal({
  open,
  onClose,
  region,
}: {
  open: boolean;
  onClose: () => void;
  region?: Region | null;
}) {
  const queryClient = useQueryClient();
  const isEdit = !!region;
  const [name, setName] = useState(region?.name ?? "");
  const [code, setCode] = useState(region?.code ?? "");
  const [statesText, setStatesText] = useState(region?.states.join(", ") ?? "");

  const mutation = useMutation({
    mutationFn: async () => {
      const states = statesText.split(",").map((s) => s.trim()).filter(Boolean);
      const payload = { name, code, states };
      if (isEdit) {
        const r = await apiClient.patch(`/regions/${region!.id}`, payload);
        return r.data;
      } else {
        const r = await apiClient.post("/regions", payload);
        return r.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["regions"] });
      toast({ title: isEdit ? "Region updated" : "Region created" });
      onClose();
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Region" : "Create Region"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Region Code *</label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. NR, SR, WR" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Region Name *</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Northern Region" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">States (comma-separated)</label>
            <Textarea value={statesText} onChange={(e) => setStatesText(e.target.value)} placeholder="e.g. Delhi, Haryana, Punjab, Uttar Pradesh" rows={3} />
            <p className="text-xs text-gray-400 mt-1">Enter state names separated by commas</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => mutation.mutate()} disabled={!name.trim() || !code.trim() || mutation.isPending} isLoading={mutation.isPending}>
            {isEdit ? "Update" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Bureaus tab ───────────────────────────────────────────────────────────────

function BureausTab() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editBureau, setEditBureau] = useState<Bureau | null>(null);
  const [deleteBureau, setDeleteBureau] = useState<Bureau | null>(null);

  const { data: bureaus, isLoading } = useQuery({
    queryKey: ["bureaus"],
    queryFn: async () => {
      const r = await apiClient.get<Bureau[]>("/bureaus");
      return r.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/bureaus/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bureaus"] });
      toast({ title: "Bureau deleted" });
      setDeleteBureau(null);
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  if (isLoading)
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Add Bureau
        </Button>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {bureaus?.map((bureau) => (
          <Card key={bureau.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-4 w-4 text-gray-400" />
                <span className="truncate">{bureau.name}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Code</span>
                  <Badge variant="secondary">{bureau.code}</Badge>
                </div>
                {bureau.description && (
                  <p className="text-gray-500 text-xs">{bureau.description}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Status</span>
                  <Badge variant={bureau.is_active ? "success" : "secondary"}>
                    {bureau.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditBureau(bureau)}
                  >
                    <Edit className="mr-1 h-3.5 w-3.5" /> Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteBureau(bureau)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="mr-1 h-3.5 w-3.5" /> Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {bureaus?.length === 0 && (
          <p className="col-span-3 text-center text-sm text-gray-400 py-8">
            No bureaus configured. Add your first bureau.
          </p>
        )}
      </div>

      <BureauModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <BureauModal open={!!editBureau} onClose={() => setEditBureau(null)} bureau={editBureau} />

      <AlertDialog open={!!deleteBureau} onOpenChange={() => setDeleteBureau(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Bureau</AlertDialogTitle>
            <AlertDialogDescription>
              Delete bureau <strong>{deleteBureau?.name}</strong>? This cannot be undone and will
              fail if the bureau has associated cases.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              onClick={() => deleteBureau && deleteMutation.mutate(deleteBureau.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ── Regions tab ───────────────────────────────────────────────────────────────

function RegionsTab() {
  const [createOpen, setCreateOpen] = useState(false);
  const [editRegion, setEditRegion] = useState<Region | null>(null);

  const { data: regions, isLoading } = useQuery({
    queryKey: ["regions"],
    queryFn: async () => {
      const r = await apiClient.get<Region[]>("/regions");
      return r.data;
    },
  });

  if (isLoading)
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Add Region
        </Button>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {regions?.map((region) => (
          <Card key={region.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="h-4 w-4 text-gray-400" />
                <span className="truncate">{region.name}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Code</span>
                  <Badge variant="secondary">{region.code}</Badge>
                </div>
                {region.states.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-400 mb-1">States</p>
                    <div className="flex flex-wrap gap-1">
                      {region.states.slice(0, 4).map((s) => (
                        <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                      ))}
                      {region.states.length > 4 && (
                        <Badge variant="outline" className="text-xs">
                          +{region.states.length - 4} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditRegion(region)}
                  >
                    <Edit className="mr-1 h-3.5 w-3.5" /> Edit
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {regions?.length === 0 && (
          <p className="col-span-3 text-center text-sm text-gray-400 py-8">
            No regions configured.
          </p>
        )}
      </div>

      <RegionModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <RegionModal open={!!editRegion} onClose={() => setEditRegion(null)} region={editRegion} />
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function BureauConfigPage() {
  return (
    <div>
      <PageHeader
        title="Bureau & Region Configuration"
        subtitle="Manage bureaus, cells, and regional office assignments"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Administration" },
          { label: "Bureaus & Regions" },
        ]}
      />

      <div className="p-6">
        <Tabs defaultValue="bureaus">
          <TabsList className="mb-6">
            <TabsTrigger value="bureaus">Bureaus</TabsTrigger>
            <TabsTrigger value="regions">Regions</TabsTrigger>
          </TabsList>

          <TabsContent value="bureaus">
            <BureausTab />
          </TabsContent>
          <TabsContent value="regions">
            <RegionsTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
