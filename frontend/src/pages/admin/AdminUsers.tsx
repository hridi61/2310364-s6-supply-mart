import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import Alert from "../../components/Alert";
import Pagination from "../../components/Pagination";
import { bulkUsers, downloadCsv, listUsers } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { AdminUser, Paged } from "../../types";
import { formatDate, toBn } from "../../utils/format";

const PAGE_SIZE = 10;

export default function AdminUsers() {
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paged<AdminUser> | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const load = useCallback(() => {
    listUsers({ q: search, role, status, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })
      .then(setData)
      .catch((e) => setError(messageOf(e)));
  }, [search, role, status, page]);
  useEffect(load, [load]);

  function submitSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearch(q.trim());
  }

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function bulk(action: "ban" | "unban") {
    if (selected.size === 0) return;
    let reason: string | undefined;
    if (action === "ban") {
      const input = window.prompt(`${toBn(selected.size)} জনকে ban করার কারণ লিখুন:`);
      if (input === null) return;
      reason = input.trim();
      if (reason.length < 3) return setError("কারণ কমপক্ষে ৩ অক্ষরের হতে হবে");
    }
    try {
      const result = await bulkUsers(action, [...selected], reason);
      setError("");
      setFlash(
        `${toBn(result.done.length)} জনের কাজ হয়েছে` +
          (result.skipped.length ? `, ${toBn(result.skipped.length)}টি বাদ (অ্যাডমিন বা পাওয়া যায়নি)` : ""),
      );
      setSelected(new Set());
      load();
    } catch (e) {
      setFlash("");
      setError(messageOf(e));
    }
  }

  async function exportCsv() {
    try {
      await downloadCsv("users", { q: search, role, status }); // একই ফিল্টার মেনে
    } catch (e) {
      setError(messageOf(e));
    }
  }

  return (
    <>
      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="card filters">
        <form onSubmit={submitSearch} className="search">
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="নাম বা ইমেইল খুঁজুন" aria-label="খুঁজুন" />
          <button type="submit" className="btn">
            খুঁজুন
          </button>
        </form>
        <select value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }} aria-label="role">
          <option value="">সব role</option>
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="অবস্থা">
          <option value="">সব অবস্থা</option>
          <option value="active">সক্রিয়</option>
          <option value="banned">ban করা</option>
        </select>
      </div>

      <div className="toolbar">
        <span className="muted">নির্বাচিত: {toBn(selected.size)}</span>
        <button type="button" className="btn btn-danger" disabled={selected.size === 0} onClick={() => bulk("ban")}>
          ban করুন
        </button>
        <button type="button" className="btn" disabled={selected.size === 0} onClick={() => bulk("unban")}>
          unban করুন
        </button>
        <button type="button" className="btn push" onClick={exportCsv}>
          CSV ডাউনলোড
        </button>
      </div>

      {data === null && !error ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : data && data.items.length === 0 ? (
        <div className="card empty">
          <p>এই ফিল্টারে কোনো ব্যবহারকারী নেই।</p>
        </div>
      ) : (
        data && (
          <>
            <p className="muted">মোট {toBn(data.total)} জন</p>
            <div className="card table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        aria-label="সব বাছুন"
                        checked={data.items.length > 0 && data.items.every((u) => selected.has(u.id))}
                        onChange={(e) => setSelected(e.target.checked ? new Set(data.items.map((u) => u.id)) : new Set())}
                      />
                    </th>
                    <th>নাম</th>
                    <th>role</th>
                    <th>অবস্থা</th>
                    <th>শেষ লগইন</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <input type="checkbox" aria-label={`${u.name} বাছুন`} checked={selected.has(u.id)} onChange={() => toggle(u.id)} />
                      </td>
                      <td>
                        <Link to={`/admin/users/${u.id}`}>{u.name}</Link>
                        <br />
                        <span className="muted small">{u.email}</span>
                      </td>
                      <td>
                        <span className={u.role === "admin" ? "badge badge-on" : "badge"}>{u.role}</span>
                      </td>
                      <td>{u.is_banned ? <span className="badge badge-bad">ban</span> : <span className="badge badge-on">সক্রিয়</span>}</td>
                      <td>{u.last_login_at ? formatDate(u.last_login_at) : "—"}</td>
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
