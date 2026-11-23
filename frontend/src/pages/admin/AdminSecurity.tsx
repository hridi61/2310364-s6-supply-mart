import { useEffect, useState } from "react";
import Alert from "../../components/Alert";
import { getSecurity } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { SecurityOverview } from "../../types";
import { formatDate, toBn } from "../../utils/format";

export default function AdminSecurity() {
  const [days, setDays] = useState(7);
  const [data, setData] = useState<SecurityOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    getSecurity(days)
      .then(setData)
      .catch((e) => setError(messageOf(e)));
  }, [days]);

  return (
    <>
      <div className="toolbar">
        <label>
          সময়সীমা{" "}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={1}>গত ১ দিন</option>
            <option value={7}>গত ৭ দিন</option>
            <option value={30}>গত ৩০ দিন</option>
          </select>
        </label>
      </div>
      {error && <Alert kind="error">{error}</Alert>}
      {!data && !error && <p className="muted">লোড হচ্ছে...</p>}
      {data && (
        <>
          <h2>IP অনুযায়ী ভুল লগইন</h2>
          {data.by_ip.length === 0 ? <p className="muted">কোনো ভুল লগইন নেই।</p> : (
            <div className="card table-wrap"><table className="table">
              <thead><tr><th>IP</th><th>ভুল চেষ্টা</th><th>কয়টি অ্যাকাউন্টে</th></tr></thead>
              <tbody>{data.by_ip.map((r) => <tr key={r.ip ?? "?"}><td>{r.ip ?? "অজানা"}</td><td>{toBn(r.failures)}</td><td>{toBn(r.accounts)}</td></tr>)}</tbody>
            </table></div>
          )}

          <h2 className="section">অ্যাকাউন্ট অনুযায়ী ভুল লগইন</h2>
          {data.by_account.length === 0 ? <p className="muted">কোনো ভুল লগইন নেই।</p> : (
            <div className="card table-wrap"><table className="table">
              <thead><tr><th>ইমেইল</th><th>ভুল চেষ্টা</th><th>সবশেষ</th></tr></thead>
              <tbody>{data.by_account.map((r) => <tr key={r.email}><td>{r.email}</td><td>{toBn(r.failures)}</td><td>{formatDate(r.last_at)}</td></tr>)}</tbody>
            </table></div>
          )}

          <h2 className="section">এখন লক হয়ে থাকা অ্যাকাউন্ট</h2>
          {data.locked_accounts.length === 0 ? <p className="muted">কোনো অ্যাকাউন্ট লক নেই।</p> : (
            <ul className="plain">{data.locked_accounts.map((a) => <li key={a.id}>{a.email} <span className="muted small">· লক থাকবে {formatDate(a.locked_until)} পর্যন্ত</span></li>)}</ul>
          )}
        </>
      )}
    </>
  );
}
