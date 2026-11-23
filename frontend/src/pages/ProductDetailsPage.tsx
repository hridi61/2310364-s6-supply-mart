import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import Alert from "../components/Alert";
import { ApiError, deleteProduct, getProduct, updateProduct } from "../services/api";
import { useAuth } from "../auth/AuthContext";
import type { Product } from "../types";
import { UNIT_LABEL, formatDate, formatPrice, toBn } from "../utils/format";
import NotFoundPage from "./NotFoundPage";

function messageOf(err: unknown): string {
  return err instanceof ApiError ? err.message : "কিছু একটা সমস্যা হয়েছে, আবার চেষ্টা করুন";
}

export default function ProductDetailsPage() {
  const { id } = useParams();
  const productId = Number(id);
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stockInput, setStockInput] = useState("");

  const initialFlash = (location.state as { flash?: string } | null)?.flash ?? "";
  const [flash, setFlash] = useState(initialFlash);
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialFlash) {
      navigate({ pathname: location.pathname, search: location.search }, { replace: true, state: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (!Number.isInteger(productId)) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    setLoading(true);
    getProduct(productId)
      .then((result) => {
        if (cancelled) return;
        setProduct(result);
        setStockInput(String(result.stock));
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(messageOf(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [productId]);

  async function toggleActive() {
    if (!product) return;
    try {
      const updated = await updateProduct(product.id, { is_active: !product.is_active });
      setProduct(updated);
      setError("");
      setFlash(updated.is_active ? "পণ্য চালু করা হয়েছে" : "পণ্য বন্ধ করা হয়েছে");
    } catch (err) {
      setFlash("");
      setError(messageOf(err));
    }
  }

  async function saveStock() {
    if (!product) return;
    try {
      const updated = await updateProduct(product.id, { stock: Number(stockInput) });
      setProduct(updated);
      setError("");
      setFlash("স্টক আপডেট হয়েছে");
    } catch (err) {
      setFlash("");
      setError(messageOf(err));
    }
  }

  async function handleDelete() {
    if (!product) return;
    if (!window.confirm(`"${product.name_bn}" মুছে ফেলবেন?`)) return;
    try {
      await deleteProduct(product.id);
      navigate("/products", { state: { flash: `"${product.name_bn}" মুছে ফেলা হয়েছে` } });
    } catch (err) {
      setFlash("");
      setError(messageOf(err));
    }
  }

  if (notFound) return <NotFoundPage />;
  if (loading) return <p className="muted">লোড হচ্ছে...</p>;
  if (!product) return error ? <Alert kind="error">{error}</Alert> : null;

  return (
    <>
      <p>
        <Link to="/products">← সব পণ্য</Link>
      </p>

      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="card detail">
        <div className="detail-icon" aria-hidden>
          {product.icon}
        </div>
        <div className="detail-body">
          <h1>{product.name_bn}</h1>
          <p className="muted">{product.category_name_bn}</p>
          <p className="price">
            {formatPrice(product.price)} <span className="muted">/ {UNIT_LABEL[product.unit]}</span>
          </p>

          <dl className="facts">
            <div>
              <dt>স্টক</dt>
              <dd>{toBn(product.stock)}</dd>
            </div>
            <div>
              <dt>অবস্থা</dt>
              <dd>{product.is_active ? "চালু" : "বন্ধ"}</dd>
            </div>
            <div>
              <dt>বিক্রেতা</dt>
              <dd>{product.owner_name ?? "Supply Mart"}</dd>
            </div>
            {product.group_name && (
              <div>
                <dt>গ্রুপ</dt>
                <dd>{product.group_name}</dd>
              </div>
            )}
            <div>
              <dt>যোগ করা হয়েছে</dt>
              <dd>{formatDate(product.created_at)}</dd>
            </div>
            <div>
              <dt>শেষ বদল</dt>
              <dd>{formatDate(product.updated_at)}</dd>
            </div>
          </dl>

          {!user && <p className="muted">পণ্য বদলাতে <Link to="/login">লগইন</Link> করুন।</p>}

          <div className="actions">
            {product.can_edit && (
              <>
                <Link to={`/products/${product.id}/edit`} className="btn btn-primary">
                  সম্পাদনা
                </Link>
                <button type="button" className="btn" onClick={toggleActive}>
                  {product.is_active ? "বন্ধ করুন" : "চালু করুন"}
                </button>
              </>
            )}
            {product.can_delete && (
              <button type="button" className="btn btn-danger" onClick={handleDelete}>
                মুছুন
              </button>
            )}
          </div>

          {product.can_stock && !product.can_edit && (
            <div className="inline-form">
              <label htmlFor="stock">স্টক বদলান (আপনার অনুমতি শুধু স্টকে)</label>
              <input id="stock" type="number" min={0} value={stockInput} onChange={(e) => setStockInput(e.target.value)} />
              <button type="button" className="btn btn-primary" onClick={saveStock}>
                সংরক্ষণ
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
