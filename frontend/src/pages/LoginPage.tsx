import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Lock, Mail, LogIn } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

// ── Schema ────────────────────────────────────────────────────────────────────

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z
    .string()
    .min(1, "Password is required")
    .min(6, "Password must be at least 6 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

// ── Component ─────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const returnTo = (location.state as { returnTo?: string })?.returnTo ?? "/dashboard";

  // If already authenticated, redirect immediately
  useEffect(() => {
    if (isAuthenticated) {
      navigate(returnTo, { replace: true });
    }
  }, [isAuthenticated, navigate, returnTo]);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const {
    handleSubmit,
    formState: { isSubmitting, errors },
    setError,
  } = form;

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
      navigate(returnTo, { replace: true });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Invalid credentials. Please try again.";
      setError("root", { message });
    }
  };

  if (authLoading) return null;

  return (
    <div>
      {/* Header */}
      <div className="mb-6 text-center">
        <img
          src="/logo.png"
          alt="AICTE"
          className="mx-auto mb-3 h-16 w-16 object-contain"
        />
        <h2 className="text-xl font-bold text-gray-900">Sign In</h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter your credentials to access the portal
        </p>
      </div>

      {/* Error alert */}
      {errors.root && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{errors.root.message}</AlertDescription>
        </Alert>
      )}

      {/* Form */}
      <Form {...form}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email Address</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      {...field}
                      type="email"
                      placeholder="you@aicte.gov.in"
                      autoComplete="email"
                      className="pl-10"
                      disabled={isSubmitting}
                    />
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      {...field}
                      type="password"
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      className="pl-10"
                      disabled={isSubmitting}
                    />
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            className="w-full"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            {!isSubmitting && <LogIn className="mr-2 h-4 w-4" />}
            Sign In
          </Button>
        </form>
      </Form>

      {/* Help text */}
      <div className="mt-4 rounded-md bg-blue-50 border border-blue-200 p-3">
        <p className="text-xs text-blue-700 font-medium">Demo Credentials</p>
        <div className="mt-1 space-y-0.5 text-xs text-blue-600">
          <p>Admin: admin@aicte.gov.in / Demo@1234</p>
          <p>Officer: rb.officer@aicte.gov.in / Demo@1234</p>
        </div>
      </div>

      <p className="mt-4 text-center text-xs text-gray-400">
        This system is for authorized AICTE personnel only.
        <br />
        Unauthorized access is prohibited and may be prosecuted.
      </p>
    </div>
  );
}
