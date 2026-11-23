import { HashRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { RequireAdmin, RequireAuth } from "./auth/guards";
import Layout from "./components/Layout";
import AdminActivity from "./pages/admin/AdminActivity";
import AdminContent from "./pages/admin/AdminContent";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminLayout from "./pages/admin/AdminLayout";
import AdminSecurity from "./pages/admin/AdminSecurity";
import AdminUserDetail from "./pages/admin/AdminUserDetail";
import AdminUsers from "./pages/admin/AdminUsers";
import CategoriesPage from "./pages/CategoriesPage";
import GroupDetailPage from "./pages/GroupDetailPage";
import GroupsPage from "./pages/GroupsPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import MyProductsPage from "./pages/MyProductsPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProductDetailsPage from "./pages/ProductDetailsPage";
import ProductFormPage from "./pages/ProductFormPage";
import ProductListPage from "./pages/ProductListPage";
import ProfilePage from "./pages/ProfilePage";
import SignupPage from "./pages/SignupPage";

// HashRouter: ঠিকানা হয় /#/products। এতে Vercel-এ আলাদা rewrite ছাড়াই রিলোড ও সরাসরি লিংক কাজ করে।
export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="categories" element={<CategoriesPage />} />
            {/* পাবলিক */}
            <Route path="products" element={<ProductListPage />} />
            <Route path="products/:id" element={<ProductDetailsPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="signup" element={<SignupPage />} />

            {/* লগইন লাগে */}
            <Route element={<RequireAuth />}>
              <Route path="products/new" element={<ProductFormPage />} />
              <Route path="products/:id/edit" element={<ProductFormPage />} />
              <Route path="my-products" element={<MyProductsPage />} />
              <Route path="groups" element={<GroupsPage />} />
              <Route path="groups/:id" element={<GroupDetailPage />} />
              <Route path="profile" element={<ProfilePage />} />
            </Route>

            {/* শুধু অ্যাডমিন */}
            <Route path="admin" element={<RequireAdmin />}>
              <Route element={<AdminLayout />}>
                <Route index element={<AdminDashboard />} />
                <Route path="users" element={<AdminUsers />} />
                <Route path="users/:id" element={<AdminUserDetail />} />
                <Route path="content" element={<AdminContent />} />
                <Route path="activity" element={<AdminActivity />} />
                <Route path="security" element={<AdminSecurity />} />
              </Route>
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </HashRouter>
  );
}
