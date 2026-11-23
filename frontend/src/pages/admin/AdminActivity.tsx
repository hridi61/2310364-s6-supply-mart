import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import Alert from "../../components/Alert";
import Pagination from "../../components/Pagination";
import { downloadCsv, listActivity } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { Activity, Paged } from "../../types";
import { formatDate, shortAgent, toBn } from "../../utils/format";

const PAGE_SIZE = 15;
const ACTIONS = ["signup", "login", "login_failed", "logout", "password_change", "password_change_failed", "role_change", "ban", "unban", "delete", "export", "session_revoke", "token_reuse"];

export default function AdminActivity() {
  const [action, setAction] = useState("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paged<Activity> | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    listActivity({ action, q: search, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })
      .then(setData)
      .catch((e) => setError(messageOf(e)));
  }, [action, search, page]);
  useEffect(load, [load]);

  return (
    <>
      {error && <Alert kind="error">{error}</Alert>}
      <div className="card filters">
        <form onSubmit={(e: FormEvent) => { e.preventDefault(); setPage(1); setSearch(q.trim()); }} className="search">
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="ইমেইল, IP বা বিবরণ খুঁজুন" aria-label="খুঁজুন" />
          <button type="submit" className="btn">খুঁজুন</button>
        </form>
        <select value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }} aria-label="ঘটনার ধরন">
          <option value="">সব ঘটনা</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <button type="button" className="btn" onClick={() => downloadCsv("activity", { action, q: search }).catch((e) => setError(messageOf(e)))}>
          CSV ডাউনলোড
        </button>
      </div>

      {data === null && !error ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : data && data.items.length === 0 ? (
        <div className="card empty"><p>কোনো ঘটনা পাওয়া যায়নি।</p></div>
      ) : (
        data && (
          <>
            <p className="muted">মোট {toBn(data.total)}টি ঘটনা</p>
            <div className="card table-wrap">
              <table className="table">
                <thead><tr><th>সময়</th><th>ঘটনা</th><th>ব্যবহারকারী</th><th>IP</th><th>ব্রাউজার</th><th>বিবরণ</th></tr></thead>
                <tbody>
                  {data.items.map((a) => (
                    <tr key={a.id}>
                      <td>{formatDate(a.created_at)}</td>
                      <td><span className={a.action.includes("failed") || a.action === "ban" || a.action === "token_reuse" ? "badge badge-bad" : "badge"}>{a.action}</span></td>
                      <td>{a.email ?? "—"}</td>
                      <td>{a.ip ?? "—"}</td>
                      <td>{shortAgent(a.user_agent)}</td>
                      <td>{a.detail ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onChange={setPage} />
          </>
        )
      )}
    </>
  );
}
