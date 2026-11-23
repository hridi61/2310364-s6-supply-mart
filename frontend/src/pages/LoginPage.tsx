import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import { useAuth } from "../auth/AuthContext";
import { messageOf } from "../services/http";

export default function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/products";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (status === "authed") return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(messageOf(err));
      setBusy(false);
    }
  }

  return (
    <div className="narrow">
      <h1>লগইন</h1>
      {error && <Alert kind="error">{error}</Alert>}
      <form onSubmit={submit} className="card form" noValidate>
        <div className="field">
          <label htmlFor="email">ইমেইল</label>
          <input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">পাসওয়ার্ড</label>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button type="submit" className="btn btn-primary" disabled={busy || !email || !password}>
          {busy ? "অপেক্ষা করুন..." : "লগইন"}
        </button>
        <p className="muted">
          অ্যাকাউন্ট নেই? <Link to="/signup">সাইন আপ করুন</Link>
        </p>
      </form>
    </div>
  );
}
