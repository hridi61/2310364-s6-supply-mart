import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Alert from "../../components/Alert";
import { useAuth } from "../../auth/AuthContext";
import { banUser, changeRole, getUserDetail, revokeUserSessions, unbanUser } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { UserDetail } from "../../types";
import { formatDate, shortAgent, toBn } from "../../utils/format";

export default function AdminUserDetail() {
  const { id } = useParams();
  const userId = Number(id);
  const { user: me } = useAuth();
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");
  const [reason, setReason] = useState("");

  const load = useCallback(() => {
    getUserDetail(userId)
      .then(setDetail)
      .catch((e) => setError(messageOf(e)));
  }, [userId]);
  useEffect(load, [load]);

  async function run(action: () => Promise<unknown>, okText: string) {
    try {
      await action();
      setError("");
      setFlash(okText);
      load();
    } catch (e) {
      setFlash("");
      setError(messageOf(e));
    }
  }

  if (!detail) return error ? <Alert kind="error">{error}</Alert> : <p className="muted">লোড হচ্ছে...</p>;
  const u = detail.user;
  const isSelf = me?.id === u.id;

  return (
    <>
      <p>
        <Link to="/admin/users">← সব ব্যবহারকারী</Link>
      </p>
      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="card">
        <h2>
          {u.name} {isSelf && <span className="muted small">(আপনি)</span>}
        </h2>
        <dl className="facts">
          <div><dt>ইমেইল</dt><dd>{u.email}</dd></div>
          <div><dt>role</dt><dd>{u.role}</dd></div>
          <div><dt>অবস্থা</dt><dd>{u.is_banned ? `ban (${u.ban_reason ?? ""})` : "সক্রিয়"}</dd></div>
          <div><dt>যোগ দিয়েছেন</dt><dd>{formatDate(u.created_at)}</dd></div>
          <div><dt>শেষ লগইন</dt><dd>{u.last_login_at ? formatDate(u.last_login_at) : "—"}</dd></div>
        </dl>

        <div className="actions">
          {u.is_banned ? (
            <button type="button" className="btn btn-primary" onClick={() => run(() => unbanUser(u.id), "unban করা হয়েছে")}>
              unban করুন
            </button>
          ) : (
            <form
              className="inline-form"
              onSubmit={(e) => {
                e.preventDefault();
                run(() => banUser(u.id, reason.trim()), "ban করা হয়েছে").then(() => setReason(""));
              }}
            >
              <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="ban-এর কারণ (বাধ্যতামূলক)" aria-label="ban-এর কারণ" maxLength={300} />
              <button type="submit" className="btn btn-danger" disabled={reason.trim().length < 3 || u.role === "admin"}>
                ban করুন
              </button>
            </form>
          )}
          <button type="button" className="btn" disabled={isSelf} onClick={() => run(() => changeRole(u.id, u.role === "admin" ? "user" : "admin"), "role বদলেছে")}>
            {u.role === "admin" ? "সাধারণ ব্যবহারকারী করুন" : "অ্যাডমিন বানান"}
          </button>
          <button type="button" className="btn" onClick={() => run(() => revokeUserSessions(u.id), "সব সেশন বন্ধ হয়েছে")}>
            সব সেশন বন্ধ করুন
          </button>
        </div>
        {(isSelf || u.role === "admin") && (
          <p className="muted small">নিয়ম: অ্যাডমিন নিজের role বদলাতে পারে না, আর কোনো অ্যাডমিনকে ban করা যায় না।</p>
        )}
      </div>

      <h2 className="section">পণ্য ({toBn(detail.products.length)})</h2>
      {detail.products.length === 0 ? <p className="muted">কোনো পণ্য নেই।</p> : (
        <ul className="plain">
          {detail.products.map((p) => (
            <li key={p.id}><Link to={`/products/${p.id}`}>{p.name_bn}</Link> <span className="muted small">৳{toBn(p.price)} · স্টক {toBn(p.stock)}</span></li>
          ))}
        </ul>
      )}

      <h2 className="section">গ্রুপ ({toBn(detail.groups.length)})</h2>
      {detail.groups.length === 0 ? <p className="muted">কোনো গ্রুপে নেই।</p> : (
        <ul className="plain">
          {detail.groups.map((g) => (
            <li key={`${g.id}-${g.role}`}>{g.name} <span className="muted small">· {g.role} · {g.permissions}</span></li>
          ))}
        </ul>
      )}

      <h2 className="section">চালু সেশন ({toBn(detail.sessions.length)})</h2>
      {detail.sessions.length === 0 ? <p className="muted">কোনো চালু সেশন নেই।</p> : (
        <div className="card table-wrap">
          <table className="table">
            <thead><tr><th>ব্রাউজার</th><th>IP</th><th>শুরু</th><th>শেষ ব্যবহার</th></tr></thead>
            <tbody>
              {detail.sessions.map((s) => (
                <tr key={s.id}><td>{shortAgent(s.user_agent)}</td><td>{s.ip ?? "—"}</td><td>{formatDate(s.created_at)}</td><td>{formatDate(s.last_used_at)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2 className="section">সাম্প্রতিক অ্যাক্টিভিটি</h2>
      <div className="card table-wrap">
        <table className="table">
          <thead><tr><th>সময়</th><th>ঘটনা</th><th>IP</th><th>বিবরণ</th></tr></thead>
          <tbody>
            {detail.activity.map((a) => (
              <tr key={a.id}><td>{formatDate(a.created_at)}</td><td><span className="badge">{a.action}</span></td><td>{a.ip ?? "—"}</td><td>{a.detail ?? ""}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
