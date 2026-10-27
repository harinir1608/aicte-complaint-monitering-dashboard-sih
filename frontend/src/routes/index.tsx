import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { AppLayout } from "@/layouts/AppLayout";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Loader2 } from "lucide-react";

// ── Lazy-loaded pages ─────────────────────────────────────────────────────────

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

// Protected pages (code-split)
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const InstitutionListPage = lazy(() => import("@/pages/InstitutionListPage"));
const InstitutionFormPage = lazy(() => import("@/pages/InstitutionFormPage"));
const InstitutionProfilePage = lazy(() => import("@/pages/InstitutionProfilePage"));
const ComplaintListPage = lazy(() => import("@/pages/ComplaintListPage"));
const ComplaintFormPage = lazy(() => import("@/pages/ComplaintFormPage"));
const ComplaintDetailPage = lazy(() => import("@/pages/ComplaintDetailPage"));
const CaseListPage = lazy(() => import("@/pages/CaseListPage"));
const CaseDetailPage = lazy(() => import("@/pages/CaseDetailPage"));
const OverlapListPage = lazy(() => import("@/pages/OverlapListPage"));
const OverlapDetailPage = lazy(() => import("@/pages/OverlapDetailPage"));
const ConflictListPage = lazy(() => import("@/pages/ConflictListPage"));
const ConflictDetailPage = lazy(() => import("@/pages/ConflictDetailPage"));
const ReportsPage = lazy(() => import("@/pages/ReportsPage"));
const NotificationsPage = lazy(() => import("@/pages/NotificationsPage"));

// Admin pages
const UserManagementPage = lazy(() => import("@/pages/admin/UserManagementPage"));
const BureauConfigPage = lazy(() => import("@/pages/admin/BureauConfigPage"));
const SLAConfigPage = lazy(() => import("@/pages/admin/SLAConfigPage"));
const AuditLogPage = lazy(() => import("@/pages/admin/AuditLogPage"));

// ── Loading fallback ──────────────────────────────────────────────────────────

function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center py-24">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );
}

// ── Router ────────────────────────────────────────────────────────────────────

export function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public auth routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>

        {/* Protected app routes */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Root redirect */}
          <Route index element={<Navigate to="/dashboard" replace />} />

          {/* Dashboard */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Institutions */}
          <Route path="/institutions" element={<InstitutionListPage />} />
          <Route path="/institutions/new" element={<InstitutionFormPage />} />
          <Route path="/institutions/:id" element={<InstitutionProfilePage />} />
          <Route path="/institutions/:id/edit" element={<InstitutionFormPage />} />

          {/* Complaints */}
          <Route path="/complaints" element={<ComplaintListPage />} />
          <Route path="/complaints/new" element={<ComplaintFormPage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />

          {/* Cases */}
          <Route path="/cases" element={<CaseListPage />} />
          <Route path="/cases/:id" element={<CaseDetailPage />} />

          {/* Overlaps */}
          <Route path="/overlaps" element={<OverlapListPage />} />
          <Route path="/overlaps/:id" element={<OverlapDetailPage />} />

          {/* Conflicts */}
          <Route path="/conflicts" element={<ConflictListPage />} />
          <Route path="/conflicts/:id" element={<ConflictDetailPage />} />

          {/* Reports */}
          <Route path="/reports" element={<ReportsPage />} />

          {/* Notifications */}
          <Route path="/notifications" element={<NotificationsPage />} />

          {/* Admin - role gated */}
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requiredRoles={["admin", "system_administrator"]}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/bureaus"
            element={
              <ProtectedRoute requiredRoles={["admin", "system_administrator"]}>
                <BureauConfigPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/sla"
            element={
              <ProtectedRoute requiredRoles={["admin", "system_administrator"]}>
                <SLAConfigPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/audit"
            element={
              <ProtectedRoute requiredRoles={["admin", "system_administrator"]}>
                <AuditLogPage />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}

export default AppRoutes;
