import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-react";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="text-center max-w-md">
        {/* 404 graphic */}
        <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-indigo-100">
          <span className="text-4xl font-black text-indigo-600">404</span>
        </div>

        <h1 className="text-2xl font-bold text-gray-900">Page Not Found</h1>
        <p className="mt-3 text-gray-500">
          The page you are looking for does not exist or has been moved.
          Please check the URL or navigate back to the dashboard.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Go Back
          </Button>
          <Button onClick={() => navigate("/dashboard")}>
            <Home className="mr-2 h-4 w-4" />
            Go to Dashboard
          </Button>
        </div>

        <div className="mt-8 border-t border-gray-200 pt-6">
          <p className="text-sm text-gray-400">
            AICTE Integrated Complaint Monitoring Dashboard
          </p>
          <p className="text-xs text-gray-400 mt-1">
            If you believe this is an error, please contact the system administrator.
          </p>
        </div>
      </div>
    </div>
  );
}
