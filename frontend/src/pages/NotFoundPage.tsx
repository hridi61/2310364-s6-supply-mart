import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="card empty">
      <p className="empty-icon" aria-hidden>
        🛒
      </p>
      <h1>পেজটি খুঁজে পাওয়া যায়নি</h1>
      <p className="muted">আপনি যে ঠিকানাটি খুঁজছেন সেটি নেই বা সরিয়ে নেওয়া হয়েছে।</p>
      <Link to="/products" className="btn btn-primary">
        সব পণ্যে ফিরে যান
      </Link>
    </div>
  );
}