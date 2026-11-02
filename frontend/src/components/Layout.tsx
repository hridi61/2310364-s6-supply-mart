import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <>
      <header className="header">
        <div className="container header-inner">
          <NavLink to="/products" className="brand">
            🛍️ Supply Mart
          </NavLink>
          <nav className="nav" aria-label="প্রধান মেনু">
            <NavLink to="/products" end>
              সব পণ্য
            </NavLink>
            <NavLink to="/products/new">নতুন পণ্য</NavLink>
          </nav>
        </div>
      </header>

      <main className="container main">
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container">Supply Mart — মুদির সব পণ্য, এক জায়গায় (MVP)</div>
      </footer>
    </>
  );
}