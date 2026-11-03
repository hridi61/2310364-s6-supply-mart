import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Alert from "../components/Alert";
import ProductForm from "../components/ProductForm";
import { ApiError, createProduct, getProduct, listCategories, updateProduct } from "../services/api";
import type { Category, Product, ProductInput } from "../types";
import NotFoundPage from "./NotFoundPage";

// /products/new (নতুন) এবং /products/:id/edit (সম্পাদনা), দুটোই এই পেজ
export default function ProductFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const editing = id !== undefined;
  const productId = Number(id);

  const [categories, setCategories] = useState<Category[]>([]);
  const [product, setProduct] = useState<Product | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (editing && !Number.isInteger(productId)) {
        setNotFound(true);
        setLoading(false);
        return;
      }
      try {
        const loadedCategories = await listCategories();
        const loadedProduct = editing ? await getProduct(productId) : undefined;
        if (cancelled) return;
        setCategories(loadedCategories);
        setProduct(loadedProduct);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err instanceof ApiError ? err.message : "তথ্য আনা যায়নি");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [editing, productId]);

  async function handleSubmit(input: ProductInput) {
    setSubmitting(true);
    setError("");
    setServerErrors({});
    try {
      const saved = editing ? await updateProduct(productId, input) : await createProduct(input);
      navigate(`/products/${saved.id}`, {
        state: { flash: editing ? "পণ্য আপডেট হয়েছে" : "নতুন পণ্য যোগ হয়েছে" },
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setServerErrors(err.fields);
      } else {
        setError("কিছু একটা সমস্যা হয়েছে, আবার চেষ্টা করুন");
      }
      setSubmitting(false);
    }
  }

  if (notFound) return <NotFoundPage />;
  if (loading) return <p className="muted">লোড হচ্ছে...</p>;

  const cancelTo = editing ? `/products/${productId}` : "/products";

  return (
    <>
      <p>
        <Link to={cancelTo}>← ফিরে যান</Link>
      </p>
      <h1>{editing ? "পণ্য সম্পাদনা" : "নতুন পণ্য যোগ করুন"}</h1>

      {error && <Alert kind="error">{error}</Alert>}

      <ProductForm
        key={product?.id ?? "new"}
        categories={categories}
        initial={product}
        submitting={submitting}
        submitLabel={editing ? "আপডেট করুন" : "পণ্য যোগ করুন"}
        serverErrors={serverErrors}
        cancelTo={cancelTo}
        onSubmit={handleSubmit}
      />
    </>
  );
}