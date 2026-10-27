import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%)" }}>

      {/* AICTE Brand Bar — matches the blue banner with Hindi + English text */}
      <div className="flex items-center gap-4 px-6 py-3" style={{ backgroundColor: "#3f51b5" }}>
        <img
          src="/logo.png"
          alt="AICTE Logo"
          className="h-14 w-14 object-contain shrink-0"
        />
        <div>
          <div
            className="font-bold text-white leading-tight"
            style={{ fontSize: "1.15rem", fontFamily: "'Noto Sans Devanagari', 'Mangal', sans-serif" }}
          >
            अखिल भारतीय तकनीकी शिक्षा परिषद्
          </div>
          <div className="text-sm text-blue-100 leading-tight tracking-wide">
            All India Council for Technical Education
          </div>
        </div>
        <div className="ml-auto text-right hidden sm:block">
          <div className="text-xs text-blue-200">Ministry of Education</div>
          <div className="text-xs font-medium text-white">Government of India</div>
        </div>
      </div>

      {/* Thin saffron accent line */}
      <div className="h-1" style={{ background: "linear-gradient(to right, #ff9800, #f44336, #ff9800)" }} />

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-xl font-bold text-white leading-snug">
              Integrated Institution Complaint<br />Monitoring &amp; Status Dashboard
            </h1>
            <p className="mt-2 text-blue-200 text-sm">
              Secure access for authorized AICTE personnel only
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-2xl p-8">
            <Outlet />
          </div>

          <p className="mt-5 text-center text-blue-300 text-xs">
            For technical assistance, contact your system administrator.
            <br />
            This portal is for authorized use only.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-3 text-xs text-blue-300" style={{ backgroundColor: "rgba(0,0,0,0.3)" }}>
        &copy; {new Date().getFullYear()} अखिल भारतीय तकनीकी शिक्षा परिषद् &nbsp;|&nbsp; All India Council for Technical Education
      </div>
    </div>
  );
}

export default AuthLayout;
