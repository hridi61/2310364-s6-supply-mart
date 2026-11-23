import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, status, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <>
      <header className="header">
        <div className="container header-inner">
          <NavLink to="/" className="brand">
            🛍️ Supply Mart
          </NavLink>
          {/* মেনু role অনুযায়ী বদলায় (শুধু সুবিধা; আসল নিয়ম সার্ভারে) */}
          <nav className="nav" aria-label="প্রধান মেনু">
            <NavLink to="/" end>
              হোম
            </NavLink>
            <NavLink to="/products">পণ্য</NavLink>
            <NavLink to="/categories">ক্যাটাগরি</NavLink>
            {user && (
              <>
                <NavLink to="/my-products">আমার পণ্য</NavLink>
                <NavLink to="/groups">গ্রুপ</NavLink>
                <NavLink to="/profile">প্রোফাইল</NavLink>
              </>
            )}
            {isAdmin && <NavLink to="/admin">অ্যাডমিন</NavLink>}
          </nav>
          <div className="nav-user">
            {status === "loading" && <span className="muted">...</span>}
            {status === "guest" && (
              <>
                <NavLink to="/login">লগইন</NavLink>
                <NavLink to="/signup" className="btn btn-primary">
                  সাইন আপ
                </NavLink>
              </>
            )}
            {user && (
              <>
                <span className="who">
                  {user.name} {isAdmin && <span className="badge badge-on">অ্যাডমিন</span>}
                </span>
                <button type="button" className="btn" onClick={handleLogout}>
                  লগআউট
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="container main">
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container hm-footer">
          <div>
            <p className="hm-footer-brand">🛍️ Supply Mart</p>
            <p>মুদির সব পণ্য, এক জায়গায়। এটি একটি ডেমো প্রজেক্ট: আসল পেমেন্ট বা ডেলিভারি নেই।</p>
          </div>
          <div>
            <h3>কেনাকাটা</h3>
            <ul>
              <li><Link to="/">হোম</Link></li>
              <li><Link to="/products">সব পণ্য</Link></li>
              <li><Link to="/categories">ক্যাটাগরি</Link></li>
            </ul>
          </div>
          <div>
            <h3>অ্যাকাউন্ট</h3>
            <ul>
              {user ? (
                <>
                  <li><Link to="/profile">প্রোফাইল</Link></li>
                  <li><Link to="/groups">আমার গ্রুপ</Link></li>
                </>
              ) : (
                <>
                  <li><Link to="/login">লগইন</Link></li>
                  <li><Link to="/signup">সাইন আপ</Link></li>
                </>
              )}
            </ul>
          </div>
          <div>
            <h3>সহায়তা</h3>
            <ul>
              <li>ইমেইল: support@supplymart.test</li>
              <li>CSE309, Independent University, Bangladesh</li>
            </ul>
          </div>
        </div>
        <div className="container hm-copy">© 2026 Supply Mart · Autumn 2026 course project</div>
      </footer>
    </>
  );
}
