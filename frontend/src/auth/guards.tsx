import { Navigate, Outlet, useLocation } from "react-router-dom";
import ForbiddenPage from "../pages/ForbiddenPage";
import { useAuth } from "./AuthContext";

// UI-র সুবিধার জন্য: আসল নিরাপত্তা সার্ভারে (প্রতিটি endpoint নিজে role/অনুমতি দেখে)

export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <p className="muted">সেশন যাচাই হচ্ছে...</p>; // অতিথি পেজের ঝলক নেই
  if (status === "guest") return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return <Outlet />;
}

export function RequireAdmin() {
  const { status, isAdmin } = useAuth();
  const location = useLocation();
  if (status === "loading") return <p className="muted">সেশন যাচাই হচ্ছে...</p>;
  if (status === "guest") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (!isAdmin) return <ForbiddenPage />;
  return <Outlet />;
}
