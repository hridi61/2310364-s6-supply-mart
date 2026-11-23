import { useEffect, useState } from "react";
import Alert from "../../components/Alert";
import { getStats } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { AdminStats } from "../../types";
import { toBn } from "../../utils/format";

const CARDS: { key: keyof AdminStats; label: string; warn?: boolean }[] = [
  { key: "users", label: "মোট ব্যবহারকারী" },
  { key: "admins", label: "অ্যাডমিন" },
  { key: "banned_users", label: "ban করা ব্যবহারকারী", warn: true },
  { key: "products", label: "মোট পণ্য" },
  { key: "groups", label: "মোট গ্রুপ" },
  { key: "new_users_7d", label: "গত ৭ দিনে নতুন ব্যবহারকারী" },
  { key: "new_products_7d", label: "গত ৭ দিনে নতুন পণ্য" },
  { key: "new_groups_7d", label: "গত ৭ দিনে নতুন গ্রুপ" },
  { key: "active_sessions", label: "চালু সেশন" },
  { key: "failed_logins_24h", label: "গত ২৪ ঘণ্টায় ভুল লগইন", warn: true },
];

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((e) => setError(messageOf(e)));
  }, []);

  if (error) return <Alert kind="error">{error}</Alert>;
  if (!stats) return <p className="muted">লোড হচ্ছে...</p>;

  return (
    <div className="stats">
      {CARDS.map((c) => (
        <div key={c.key} className={`card stat${c.warn && stats[c.key] > 0 ? " stat-warn" : ""}`}>
          <span className="stat-num">{toBn(stats[c.key])}</span>
          <span className="muted">{c.label}</span>
        </div>
      ))}
    </div>
  );
}
