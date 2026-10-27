import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getInstitution,
  createInstitution,
  updateInstitution,
  addInstitutionAlias,
} from "@/api/institutions";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "@/hooks/use-toast";
import { Save, ArrowLeft, Plus, AlertCircle } from "lucide-react";

// ── Schema ────────────────────────────────────────────────────────────────────

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  permanent_id: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  district: z.string().optional(),
  state: z.string().optional(),
  institution_type: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  website: z.string().url("Invalid URL").optional().or(z.literal("")),
});

type FormData = z.infer<typeof schema>;

const INSTITUTION_TYPES = [
  "Engineering", "Management", "Pharmacy", "Architecture",
  "Hotel Management", "Applied Arts", "MCA", "Other",
];

const STATES = [
  "Andhra Pradesh", "Assam", "Bihar", "Delhi", "Gujarat", "Haryana",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha",
  "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh",
  "West Bengal",
];

const ALIAS_TYPES = [
  { value: "abbreviation", label: "Abbreviation" },
  { value: "former_name", label: "Former Name" },
  { value: "common_name", label: "Common Name" },
  { value: "other", label: "Other" },
];

// ── Alias section ─────────────────────────────────────────────────────────────

function AliasesSection({
  institutionId,
  existingAliases,
}: {
  institutionId?: string;
  existingAliases: { id: string; alias: string; alias_type: string }[];
}) {
  const queryClient = useQueryClient();
  const [newAlias, setNewAlias] = useState("");
  const [newAliasType, setNewAliasType] = useState("abbreviation");

  const addMutation = useMutation({
    mutationFn: () => addInstitutionAlias(institutionId!, newAlias, newAliasType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institution", institutionId] });
      toast({ title: "Alias added" });
      setNewAlias("");
    },
    onError: (err: Error) =>
      toast({ title: "Error", description: err.message, variant: "destructive" }),
  });

  if (!institutionId) {
    return (
      <p className="text-sm text-gray-400">
        Save the institution first to add aliases.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {existingAliases.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {existingAliases.map((a) => (
            <Badge key={a.id} variant="secondary" className="gap-1">
              {a.alias}
              <span className="text-xs text-gray-400">({a.alias_type.replace(/_/g, " ")})</span>
            </Badge>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Input
          value={newAlias}
          onChange={(e) => setNewAlias(e.target.value)}
          placeholder="New alias..."
          className="flex-1"
        />
        <select
          value={newAliasType}
          onChange={(e) => setNewAliasType(e.target.value)}
          className="h-10 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {ALIAS_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <Button
          type="button"
          variant="outline"
          onClick={() => addMutation.mutate()}
          disabled={!newAlias.trim() || addMutation.isPending}
          isLoading={addMutation.isPending}
        >
          <Plus className="h-4 w-4" />
          Add
        </Button>
      </div>
    </div>
  );
}

// ── Main form ─────────────────────────────────────────────────────────────────

export default function InstitutionFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEdit = !!id;

  const { data: institution, isLoading: loadingInstitution } = useQuery({
    queryKey: ["institution", id],
    queryFn: () => getInstitution(id!),
    enabled: isEdit,
  });

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      permanent_id: "",
      address: "",
      city: "",
      district: "",
      state: "",
      institution_type: "",
      phone: "",
      email: "",
      website: "",
    },
  });

  useEffect(() => {
    if (institution) {
      form.reset({
        name: institution.name,
        permanent_id: institution.permanent_id ?? "",
        address: institution.address ?? "",
        city: institution.city ?? "",
        district: institution.district ?? "",
        state: institution.state ?? "",
        institution_type: institution.institution_type ?? "",
        phone: institution.phone ?? "",
        email: institution.email ?? "",
        website: institution.website ?? "",
      });
    }
  }, [institution, form]);

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      isEdit ? updateInstitution(id!, data) : createInstitution(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
      if (isEdit) queryClient.invalidateQueries({ queryKey: ["institution", id] });
      toast({ title: isEdit ? "Institution updated" : "Institution created" });
      navigate(`/institutions/${result.id}`);
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const onSubmit = (data: FormData) => mutation.mutate(data);

  if (loadingInstitution)
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-48 bg-gray-200 animate-pulse rounded" />
        <div className="h-64 w-full bg-gray-200 animate-pulse rounded" />
      </div>
    );

  return (
    <div>
      <PageHeader
        title={isEdit ? "Edit Institution" : "Add Institution"}
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Institutions", href: "/institutions" },
          { label: isEdit ? "Edit" : "New" },
        ]}
        actions={
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        }
      />

      <div className="p-6 max-w-3xl">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Identity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Institution Identity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Institution Name *</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Full legal name of the institution" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="permanent_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>AICTE Permanent ID</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="e.g. 1-123456789" />
                      </FormControl>
                      <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                        <AlertCircle className="h-3 w-3" />
                        Must be unique. The system will warn if this ID is already in use.
                      </p>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="institution_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Institution Type</FormLabel>
                        <FormControl>
                          <select
                            {...field}
                            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="">Select type...</option>
                            {INSTITUTION_TYPES.map((t) => (
                              <option key={t} value={t}>{t}</option>
                            ))}
                          </select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Location */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Location</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="address"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Address</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Street address" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="city"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>City</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="City" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="district"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>District</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="District" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="state"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>State</FormLabel>
                        <FormControl>
                          <select
                            {...field}
                            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="">Select state...</option>
                            {STATES.map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Contact */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Contact Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="phone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Phone</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="+91 xxxxxxxxxx" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input {...field} type="email" placeholder="contact@institution.edu.in" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <FormField
                  control={form.control}
                  name="website"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Website</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://www.institution.edu.in" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Aliases (only shown in edit mode) */}
            {isEdit && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Alternative Names & Aliases</CardTitle>
                </CardHeader>
                <CardContent>
                  <AliasesSection
                    institutionId={id}
                    existingAliases={(institution as any)?.aliases ?? []}
                  />
                </CardContent>
              </Card>
            )}

            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={mutation.isPending}>
                <Save className="mr-2 h-4 w-4" />
                {isEdit ? "Update Institution" : "Create Institution"}
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
}
