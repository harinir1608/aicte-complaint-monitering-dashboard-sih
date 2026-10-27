import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getComplaint, createCaseFromComplaint } from "@/api/complaints";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge, PriorityBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "@/hooks/use-toast";
import { formatDate, formatDateTime } from "@/lib/utils";
import {
  ArrowLeft,
  Building2,
  User,
  Tag,
  FileText,
  Briefcase,
  Plus,
  Download,
  Edit,
} from "lucide-react";

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createCaseOpen, setCreateCaseOpen] = useState(false);
  const [selectedBureauId, setSelectedBureauId] = useState("");

  const { data: complaint, isLoading } = useQuery({
    queryKey: ["complaint", id],
    queryFn: () => getComplaint(id!),
    enabled: !!id,
  });

  const createCaseMutation = useMutation({
    mutationFn: () => createCaseFromComplaint(id!, selectedBureauId),
    onSuccess: (newCase) => {
      queryClient.invalidateQueries({ queryKey: ["complaint", id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      toast({ title: "Case created", description: `Case ${newCase.case_number} created successfully` });
      setCreateCaseOpen(false);
      navigate(`/cases/${newCase.id}`);
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  if (isLoading)
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );

  if (!complaint) return <div className="p-6 text-gray-500">Complaint not found.</div>;

  return (
    <div>
      <PageHeader
        title={complaint.complaint_number}
        subtitle={complaint.subject}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Complaints", href: "/complaints" },
          { label: complaint.complaint_number },
        ]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/complaints/${id}/edit`)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
            <Button size="sm" onClick={() => setCreateCaseOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Case
            </Button>
            <Button variant="outline" onClick={() => navigate(-1)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6 max-w-5xl">
        {/* Status row */}
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Status</p>
            <StatusBadge status={complaint.status} />
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Priority</p>
            <PriorityBadge priority={complaint.priority} />
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Bureau</p>
            <p className="text-sm font-semibold text-gray-900">{complaint.bureau?.name ?? "—"}</p>
            <p className="text-xs text-gray-400">{complaint.bureau?.code ?? "—"}</p>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <p className="text-xs text-gray-400 mb-1">Received</p>
            <p className="text-sm font-semibold text-gray-900">
              {formatDate(complaint.received_date)}
            </p>
          </div>
        </div>

        <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
          {/* Main details */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Complaint Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                {complaint.institution && (
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-gray-400 shrink-0" />
                    <span className="text-gray-500">Institution:</span>
                    <Link
                      to={`/institutions/${complaint.institution.id}`}
                      className="font-medium text-indigo-600 hover:underline"
                    >
                      {complaint.institution.name}
                    </Link>
                  </div>
                )}
                {!complaint.institution && complaint.institution_name_raw && (
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-gray-400 shrink-0" />
                    <span className="text-gray-500">Institution (unverified):</span>
                    <span className="font-medium">{complaint.institution_name_raw}</span>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-gray-400 shrink-0" />
                  <span className="text-gray-500">Category:</span>
                  <span className="font-medium">{complaint.category?.name ?? "—"}</span>
                </div>

                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400 shrink-0" />
                  <span className="text-gray-500">Source:</span>
                  <span className="font-medium capitalize">{(complaint.source as string).replace(/_/g, " ")}</span>
                </div>

                {!complaint.is_anonymous && complaint.complainant_name && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400 shrink-0" />
                    <span className="text-gray-500">Complainant:</span>
                    <span className="font-medium">{complaint.complainant_name}</span>
                  </div>
                )}

                <div className="border-t pt-4">
                  <p className="text-gray-500 mb-2 font-medium">Description</p>
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {complaint.description}
                  </p>
                </div>

                <div className="border-t pt-3 text-xs text-gray-400">
                  Registered on {formatDateTime(complaint.created_at)}
                </div>
              </CardContent>
            </Card>

            {/* Documents */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  Documents
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(!complaint as any)?.documents || (complaint as any).documents?.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-4">
                    No documents uploaded.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {((complaint as any).documents ?? []).map((doc: any) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between rounded border border-gray-100 p-3"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium">{doc.filename}</p>
                            <p className="text-xs text-gray-400">
                              {(doc.file_size / 1024).toFixed(1)} KB ·{" "}
                              {formatDate(doc.uploaded_at)}
                            </p>
                          </div>
                        </div>
                        <a
                          href={`/api/v1/documents/${doc.id}/download`}
                          className="text-indigo-600 hover:underline text-xs flex items-center gap-1"
                        >
                          <Download className="h-3 w-3" /> Download
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right sidebar */}
          <div className="space-y-6">
            {/* Institution quick card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Institution</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                {complaint.institution ? (
                  <>
                    <Link
                      to={`/institutions/${complaint.institution.id}`}
                      className="font-medium text-indigo-600 hover:underline block"
                    >
                      {complaint.institution.name}
                    </Link>
                    {complaint.institution.permanent_id && (
                      <p className="text-xs text-gray-500">
                        ID: {complaint.institution.permanent_id}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-gray-500 italic">
                    {complaint.institution_name_raw ?? "Not linked"}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Linked Cases */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-gray-400" />
                  Linked Cases
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-gray-400 text-center py-2">
                  Cases generated from this complaint will appear here.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => setCreateCaseOpen(true)}
                >
                  <Plus className="mr-2 h-3.5 w-3.5" />
                  Create Case
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Create Case Modal */}
      <Dialog open={createCaseOpen} onOpenChange={setCreateCaseOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Case from Complaint</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 text-sm">
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
              <p className="text-blue-800">
                This will create a new case in the selected bureau, linked to complaint{" "}
                <strong>{complaint.complaint_number}</strong>.
              </p>
            </div>
            <div>
              <label className="font-medium text-gray-700 block mb-1">Bureau ID *</label>
              <input
                type="text"
                value={selectedBureauId}
                onChange={(e) => setSelectedBureauId(e.target.value)}
                placeholder="Enter bureau UUID"
                className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-gray-400 mt-1">
                Currently assigned bureau: {complaint.bureau?.name ?? "—"}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateCaseOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createCaseMutation.mutate()}
              disabled={!selectedBureauId.trim() || createCaseMutation.isPending}
              isLoading={createCaseMutation.isPending}
            >
              Create Case
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
