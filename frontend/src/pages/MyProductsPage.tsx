import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Alert from "../components/Alert";
import Pagination from "../components/Pagination";
import { deleteProduct, listMyProducts, messageOf } from "../services/api";
import type { ProductPage } from "../types";
import { UNIT_LABEL, formatPrice, toBn } from "../utils/format";

const PAGE_SIZE = 8;

export default function MyProductsPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ProductPage | null>(null);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const load = useCallback(() => {
    listMyProducts((page - 1) * PAGE_SIZE, PAGE_SIZE)
      .then((d) => {
        setData(d);
        if (d.items.length === 0 && page > 1) setPage(page - 1);
      })
      .catch((e) => setError(messageOf(e)));
  }, [page]);
  useEffect(load, [load]);

  async function remove(id: number, name: string) {
    if (!window.confirm(`"${name}" মুছে ফেলবেন?`)) return;
    try {
      await deleteProduct(id);
      setFlash(`"${name}" মুছে ফেলা হয়েছে`);
      setError("");
      load();
    } catch (e) {
      setFlash("");
      setError(messageOf(e));
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>আমার পণ্য</h1>
        <Link to="/products/new" className="btn btn-primary">
          + নতুন পণ্য
        </Link>
      </div>
      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}
      {data === null && !error ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : data && data.items.length === 0 ? (
        <div className="card empty">
          <p className="empty-icon" aria-hidden>
            📦
          </p>
          <h2>আপনি এখনো কোনো পণ্য যোগ করেননি</h2>
          <Link to="/products/new" className="btn btn-primary">
            প্রথম পণ্য যোগ করুন
          </Link>
        </div>
      ) : (
        data && (
          <>
            <p className="muted">মোট {toBn(data.total)}টি পণ্য (শুধু আপনার নিজের)</p>
            <div className="card table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>পণ্য</th>
                    <th>দাম</th>
                    <th>স্টক</th>
                    <th>গ্রুপ</th>
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
                      <td>
                        {formatPrice(p.price)} / {UNIT_LABEL[p.unit]}
                      </td>
                      <td>{toBn(p.stock)}</td>
                      <td>{p.group_name ?? "—"}</td>
                      <td className="row-actions">
                        <Link to={`/products/${p.id}/edit`}>সম্পাদনা</Link>
                        <button type="button" className="link-danger" onClick={() => remove(p.id, p.name_bn)}>
                          মুছুন
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onChange={setPage} />
          </>
        )
      )}
    </>
  );
}
