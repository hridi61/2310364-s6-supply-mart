import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import NotFoundPage from "./pages/NotFoundPage";
import ProductDetailsPage from "./pages/ProductDetailsPage";
import ProductFormPage from "./pages/ProductFormPage";
import ProductListPage from "./pages/ProductListPage";

// HashRouter: ঠিকানা হয় /#/products। এতে Vercel-এ আলাদা rewrite ছাড়াই রিলোড ও সরাসরি লিংক কাজ করে।
export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/products" replace />} />
          <Route path="products" element={<ProductListPage />} />
          <Route path="products/new" element={<ProductFormPage />} />
          <Route path="products/:id" element={<ProductDetailsPage />} />
          <Route path="products/:id/edit" element={<ProductFormPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}