import { Link } from "react-router-dom";

export default function ForbiddenPage() {
  return (
    <div className="card empty">
      <p className="empty-icon" aria-hidden>
        🚫
      </p>
      <h1>এই পেজে আপনার অনুমতি নেই</h1>
      <p className="muted">এই কাজটি করার অধিকার আপনার অ্যাকাউন্টের নেই।</p>
      <Link to="/products" className="btn btn-primary">
        পণ্যের তালিকায় ফিরুন
      </Link>
    </div>
  );
}
