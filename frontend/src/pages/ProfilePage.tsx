import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { FormEvent } from "react";
import Alert from "../components/Alert";
import { useAuth } from "../auth/AuthContext";
import { ApiError, messageOf } from "../services/http";
import * as authApi from "../services/auth";
import type { SessionInfo } from "../types";
import { formatDate, shortAgent } from "../utils/format";

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [profileMsg, setProfileMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [pwMsg, setPwMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [pwFields, setPwFields] = useState<Record<string, string>>({});

  const [sessions, setSessions] = useState<SessionInfo[] | null>(null);
  const [sessionError, setSessionError] = useState("");

  const loadSessions = useCallback(() => {
    authApi
      .listSessions()
      .then(setSessions)
      .catch((e) => setSessionError(messageOf(e)));
  }, []);
  useEffect(loadSessions, [loadSessions]);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    setProfileMsg(null);
    setFieldErrors({});
    try {
      const updated = await authApi.updateProfile({ name: name.trim(), phone: phone.trim() });
      setUser(updated);
      setProfileMsg({ kind: "success", text: "প্রোফাইল আপডেট হয়েছে" });
    } catch (err) {
      setProfileMsg({ kind: "error", text: messageOf(err) });
      if (err instanceof ApiError) setFieldErrors(err.fields);
    }
  }

  async function savePassword(e: FormEvent) {
    e.preventDefault();
    setPwMsg(null);
    setPwFields({});
    try {
      await authApi.changePassword(current, next);
      setCurrent("");
      setNext("");
      setPwMsg({ kind: "success", text: "পাসওয়ার্ড বদলেছে। অন্য ডিভাইসের সেশন বন্ধ করা হয়েছে।" });
      loadSessions();
    } catch (err) {
      setPwMsg({ kind: "error", text: messageOf(err) });
      if (err instanceof ApiError) setPwFields(err.fields);
    }
  }

  async function revoke(s: SessionInfo) {
    try {
      if (s.current) {
        await logout(); // এই ডিভাইসের সেশন বন্ধ করা মানে লগআউট
        navigate("/login", { replace: true });
        return;
      }
      await authApi.revokeSession(s.id);
      loadSessions();
    } catch (err) {
      setSessionError(messageOf(err));
    }
  }

  if (!user) return null;

  return (
    <>
      <h1>আমার প্রোফাইল</h1>
      <p className="muted">
        {user.email} · {user.role === "admin" ? "অ্যাডমিন" : "সাধারণ ব্যবহারকারী"}
      </p>

      <div className="grid-2 top">
        <form onSubmit={saveProfile} className="card form" noValidate>
          <h2>তথ্য বদলান</h2>
          {profileMsg && <Alert kind={profileMsg.kind}>{profileMsg.text}</Alert>}
          <div className="field">
            <label htmlFor="pname">নাম</label>
            <input id="pname" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
            {fieldErrors.name && <p className="error-text">{fieldErrors.name}</p>}
          </div>
          <div className="field">
            <label htmlFor="phone">মোবাইল (ঐচ্ছিক)</label>
            <input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="01712345678" maxLength={11} />
            {fieldErrors.phone && <p className="error-text">{fieldErrors.phone}</p>}
          </div>
          <button type="submit" className="btn btn-primary">
            সংরক্ষণ
          </button>
        </form>

        <form onSubmit={savePassword} className="card form" noValidate>
          <h2>পাসওয়ার্ড বদলান</h2>
          {pwMsg && <Alert kind={pwMsg.kind}>{pwMsg.text}</Alert>}
          <div className="field">
            <label htmlFor="cur">বর্তমান পাসওয়ার্ড</label>
            <input id="cur" type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="new">নতুন পাসওয়ার্ড</label>
            <input id="new" type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} />
            <p className="muted small">কমপক্ষে ৮ অক্ষর, একটি অক্ষর ও একটি সংখ্যা সহ।</p>
            {pwFields.new_password && <p className="error-text">{pwFields.new_password}</p>}
          </div>
          <button type="submit" className="btn btn-primary" disabled={!current || !next}>
            পাসওয়ার্ড বদলান
          </button>
        </form>
      </div>

      <h2 className="section">আমার সেশন (লগইন করা ডিভাইস)</h2>
      {sessionError && <Alert kind="error">{sessionError}</Alert>}
      {sessions === null ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : (
        <div className="card table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>ব্রাউজার</th>
                <th>IP</th>
                <th>শুরু</th>
                <th>শেষ ব্যবহার</th>
                <th>
                  <span className="sr-only">কাজ</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td>
                    {shortAgent(s.user_agent)} {s.current && <span className="badge badge-on">এই ডিভাইস</span>}
                  </td>
                  <td>{s.ip ?? "—"}</td>
                  <td>{formatDate(s.created_at)}</td>
                  <td>{formatDate(s.last_used_at)}</td>
                  <td className="row-actions">
                    <button type="button" className="link-danger" onClick={() => revoke(s)}>
                      {s.current ? "লগআউট" : "বন্ধ করুন"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
