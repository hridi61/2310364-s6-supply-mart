import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import { useAuth } from "../auth/AuthContext";
import { ApiError, messageOf } from "../services/http";

export default function SignupPage() {
  const { signup, status } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fields, setFields] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  if (status === "authed") return <Navigate to="/products" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setFields({});
    try {
      await signup(email.trim(), name.trim(), password);
      navigate("/products", { replace: true });
    } catch (err) {
      setError(messageOf(err));
      if (err instanceof ApiError) setFields(err.fields);
      setBusy(false);
    }
  }

  return (
    <div className="narrow">
      <h1>সাইন আপ</h1>
      {error && <Alert kind="error">{error}</Alert>}
      <form onSubmit={submit} className="card form" noValidate>
        <div className="field">
          <label htmlFor="name">নাম</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} autoComplete="name" />
          {fields.name && <p className="error-text">{fields.name}</p>}
        </div>
        <div className="field">
          <label htmlFor="email">ইমেইল</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          {fields.email && <p className="error-text">{fields.email}</p>}
        </div>
        <div className="field">
          <label htmlFor="password">পাসওয়ার্ড</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" />
          <p className="muted small">কমপক্ষে ৮ অক্ষর, একটি অক্ষর ও একটি সংখ্যা সহ।</p>
          {fields.password && <p className="error-text">{fields.password}</p>}
        </div>
        <button type="submit" className="btn btn-primary" disabled={busy || !email || !name || !password}>
          {busy ? "অপেক্ষা করুন..." : "অ্যাকাউন্ট খুলুন"}
        </button>
        <p className="muted">
          আগে থেকেই অ্যাকাউন্ট আছে? <Link to="/login">লগইন করুন</Link>
        </p>
      </form>
    </div>
  );
}
