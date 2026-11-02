import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import Alert from "../components/Alert";
import Pagination from "../components/Pagination";
import { ApiError, deleteProduct, listCategories, listProducts } from "../services/api";
import type { Category, Product, ProductPage, SortOption } from "../types";
import { UNIT_LABEL, formatPrice, toBn } from "../utils/format";

const PAGE_SIZE = 8;

function messageOf(err: unknown): string {
  return err instanceof ApiError ? err.message : "কিছু একটা সমস্যা হয়েছে, আবার চেষ্টা করুন";
}

export default function ProductListPage() {
  const [params, setParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  // ফিল্টারের মান URL-এ থাকে, তাই রিলোড করলে বা লিংক শেয়ার করলেও একই তালিকা আসে
  const q = params.get("q") ?? "";
  const category = params.get("category") ?? "";
  const sort = (params.get("sort") ?? "") as SortOption;
  const page = Math.max(1, Number(params.get("page") ?? 1) || 1);

  const initialFlash = (location.state as { flash?: string } | null)?.flash ?? "";
  const [flash, setFlash] = useState(initialFlash);
  const [error, setError] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<ProductPage>({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState(q);
  const [reloadKey, setReloadKey] = useState(0);

  // অন্য পেজ থেকে আসা সফলতার বার্তা একবার দেখানোর পর history থেকে সরিয়ে দিই
  useEffect(() => {
    if (initialFlash) {
      navigate({ pathname: location.pathname, search: location.search }, { replace: true, state: null });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    listProducts({ category, q, sort, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(messageOf(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [category, q, sort, page, reloadKey]);

  function updateParams(changes: Record<string, string>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    setParams(next);
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateParams({ q: searchText.trim(), page: "" });
  }

  async function handleDelete(product: Product) {
    if (!window.confirm(`"${product.name_bn}" মুছে ফেলবেন?`)) return;
    try {
      await deleteProduct(product.id);
      setError("");
      setFlash(`"${product.name_bn}" মুছে ফেলা হয়েছে`);
      // শেষ পৃষ্ঠার একমাত্র পণ্য মুছলে আগের পৃষ্ঠায় যাই
      if (data.items.length === 1 && page > 1) updateParams({ page: String(page - 1) });
      else setReloadKey((k) => k + 1);
    } catch (err) {
      setFlash("");
      setError(messageOf(err));
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>পণ্যের তালিকা</h1>
        <Link to="/products/new" className="btn btn-primary">
          + নতুন পণ্য
        </Link>
      </div>

      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="card filters">
        <form onSubmit={handleSearch} className="search">
          <input
            type="search"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="পণ্যের নাম খুঁজুন"
            aria-label="পণ্যের নাম খুঁজুন"
          />
          <button type="submit" className="btn">
            খুঁজুন
          </button>
        </form>

        <select
          value={category}
          onChange={(e) => updateParams({ category: e.target.value, page: "" })}
          aria-label="ক্যাটাগরি"
        >
          <option value="">সব ক্যাটাগরি</option>
          {categories.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.icon} {c.name_bn}
            </option>
          ))}
        </select>

        <select
          value={sort}
          onChange={(e) => updateParams({ sort: e.target.value, page: "" })}
          aria-label="সাজানো"
        >
          <option value="">নতুন আগে</option>
          <option value="price_asc">দাম: কম থেকে বেশি</option>
          <option value="price_desc">দাম: বেশি থেকে কম</option>
        </select>
      </div>

      {loading ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : data.items.length === 0 ? (
        <div className="card empty">
          <p className="empty-icon" aria-hidden>
            🔍
          </p>
          <h2>কোনো পণ্য পাওয়া যায়নি</h2>
          <p className="muted">অন্য নামে খুঁজুন বা ফিল্টার বদলান।</p>
        </div>
      ) : (
        <>
          <p className="muted">মোট {toBn(data.total)}টি পণ্য</p>
          <div className="card table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>পণ্য</th>
                  <th>ক্যাটাগরি</th>
                  <th>দাম</th>
                  <th>স্টক</th>
                  <th>অবস্থা</th>
                  <th>
                    <span className="sr-only">কাজ</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <span aria-hidden>{p.icon}</span> <Link to={`/products/${p.id}`}>{p.name_bn}</Link>
                    </td>
                    <td>{p.category_name_bn}</td>
                    <td>
                      {formatPrice(p.price)} / {UNIT_LABEL[p.unit]}
                    </td>
                    <td>{toBn(p.stock)}</td>
                    <td>
                      <span className={p.is_active ? "badge badge-on" : "badge"}>{p.is_active ? "চালু" : "বন্ধ"}</span>
                    </td>
                    <td className="row-actions">
                      <Link to={`/products/${p.id}`}>দেখুন</Link>
                      <Link to={`/products/${p.id}/edit`}>সম্পাদনা</Link>
                      <button type="button" className="link-danger" onClick={() => handleDelete(p)}>
                        মুছুন
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={data.total}
            onChange={(p) => updateParams({ page: p > 1 ? String(p) : "" })}
          />
        </>
      )}
    </>
  );
}