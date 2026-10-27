import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createComplaint } from "@/api/complaints";
import { searchInstitutions } from "@/api/institutions";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "@/hooks/use-toast";
import { ArrowLeft, Send, Search, Building2, X } from "lucide-react";
import type { Institution } from "@/types";

// ── Schema ────────────────────────────────────────────────────────────────────

const schema = z.object({
  institution_id: z.string().min(1, "Institution is required"),
  received_date: z.string().min(1, "Received date is required"),
  source: z.string().min(1, "Source is required"),
  category: z.string().min(1, "Category is required"),
  subject: z.string().min(5, "Subject must be at least 5 characters"),
  description: z.string().min(20, "Description must be at least 20 characters"),
  bureau_id: z.string().min(1, "Bureau is required"),
  priority: z.enum(["low", "medium", "high", "critical"]),
});

type FormData = z.infer<typeof schema>;

// ── Institution autocomplete ───────────────────────────────────────────────────

function InstitutionSearch({
  onChange,
}: {
  value?: string;
  onChange: (id: string, name: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Institution[]>([]);
  const [selected, setSelected] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchInstitutions(query, 8);
        setResults(data);
        setShowResults(true);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [query]);

  const handleSelect = (inst: Institution) => {
    setSelected(inst);
    setQuery(inst.name);
    setShowResults(false);
    onChange(inst.id, inst.name);
  };

  const handleClear = () => {
    setSelected(null);
    setQuery("");
    onChange("", "");
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (selected) handleClear();
          }}
          placeholder="Search institution by name or AICTE ID..."
          className="w-full h-10 rounded-md border border-gray-300 bg-white pl-10 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          onFocus={() => results.length > 0 && setShowResults(true)}
          onBlur={() => setTimeout(() => setShowResults(false), 200)}
        />
        {selected && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {showResults && (
        <div className="absolute z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg">
          {loading ? (
            <p className="px-4 py-3 text-sm text-gray-400">Searching...</p>
          ) : results.length === 0 ? (
            <p className="px-4 py-3 text-sm text-gray-400">No institutions found</p>
          ) : (
            results.map((inst) => (
              <button
                key={inst.id}
                type="button"
                className="flex w-full items-start gap-3 px-4 py-2.5 text-left hover:bg-gray-50 border-b last:border-0"
                onMouseDown={() => handleSelect(inst)}
              >
                <Building2 className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{inst.name}</p>
                  <p className="text-xs text-gray-400">
                    {[inst.permanent_id, inst.state, inst.institution_type]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {selected && (
        <div className="mt-1 flex items-center gap-1 rounded-md bg-indigo-50 border border-indigo-200 px-3 py-1.5 text-xs text-indigo-800">
          <Building2 className="h-3 w-3 shrink-0" />
          <span>Selected: {selected.name}</span>
          {selected.permanent_id && (
            <span className="text-indigo-500 ml-1">({selected.permanent_id})</span>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main form ─────────────────────────────────────────────────────────────────

const SOURCES = ["Email", "Online Portal", "Post/Letter", "Walk-in", "Phone", "Court Order", "Ministry Reference", "Other"];
const CATEGORIES = [
  "Fee Refund", "Faculty Issues", "Infrastructure", "Examination", "Affiliation",
  "Accreditation", "Admissions", "Conduct/Discipline", "Salary Dispute", "Other",
];

export default function ComplaintFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      institution_id: "",
      received_date: new Date().toISOString().split("T")[0],
      source: "",
      category: "",
      subject: "",
      description: "",
      bureau_id: "",
      priority: "medium",
    },
  });

  const mutation = useMutation({
    mutationFn: createComplaint,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["complaints"] });
      toast({ title: "Complaint registered successfully" });
      navigate(`/complaints/${result.id}`);
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  return (
    <div>
      <PageHeader
        title="Register Complaint"
        breadcrumbs={[
          { label: "Home", href: "/" },
          { label: "Complaints", href: "/complaints" },
          { label: "New" },
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
          <form
            onSubmit={form.handleSubmit((d) => mutation.mutate(d))}
            className="space-y-6"
          >
            {/* Institution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Institution</CardTitle>
              </CardHeader>
              <CardContent>
                <FormField
                  control={form.control}
                  name="institution_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Institution *</FormLabel>
                      <FormControl>
                        <InstitutionSearch
                          value={field.value}
                          onChange={(id) => field.onChange(id)}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Complaint Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Complaint Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="received_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Received Date *</FormLabel>
                        <FormControl>
                          <Input {...field} type="date" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="priority"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Priority *</FormLabel>
                        <FormControl>
                          <select
                            {...field}
                            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                          </select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="source"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Source *</FormLabel>
                        <FormControl>
                          <select
                            {...field}
                            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="">Select source...</option>
                            {SOURCES.map((s) => (
                              <option key={s} value={s}>
                                {s}
                              </option>
                            ))}
                          </select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="category"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Category *</FormLabel>
                        <FormControl>
                          <select
                            {...field}
                            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <option value="">Select category...</option>
                            {CATEGORIES.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="subject"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Subject *</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Brief subject of the complaint" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description *</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          rows={5}
                          placeholder="Detailed description of the complaint..."
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            {/* Bureau */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Bureau Assignment</CardTitle>
              </CardHeader>
              <CardContent>
                <FormField
                  control={form.control}
                  name="bureau_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Receiving Bureau ID *</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Bureau UUID" />
                      </FormControl>
                      <p className="text-xs text-gray-400 mt-1">
                        Enter the UUID of the bureau receiving this complaint
                      </p>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>

            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={mutation.isPending}>
                <Send className="mr-2 h-4 w-4" />
                Register Complaint
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
}
