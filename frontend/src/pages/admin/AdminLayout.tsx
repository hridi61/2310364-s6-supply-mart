import { NavLink, Outlet } from "react-router-dom";

export default function AdminLayout() {
  return (
    <>
      <div className="page-head">
        <h1>অ্যাডমিন ড্যাশবোর্ড</h1>
      </div>
      <nav className="subnav" aria-label="অ্যাডমিন মেনু">
        <NavLink to="/admin" end>
          সারসংক্ষেপ
        </NavLink>
        <NavLink to="/admin/users">ব্যবহারকারী</NavLink>
        <NavLink to="/admin/content">কনটেন্ট</NavLink>
        <NavLink to="/admin/activity">অ্যাক্টিভিটি লগ</NavLink>
        <NavLink to="/admin/security">নিরাপত্তা</NavLink>
      </nav>
      <Outlet />
    </>
  );
}
