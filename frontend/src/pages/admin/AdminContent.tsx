import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import Alert from "../../components/Alert";
import Pagination from "../../components/Pagination";
import { bulkDeleteGroups, bulkDeleteProducts, downloadCsv, listAdminGroups, listAdminProducts } from "../../services/admin";
import { messageOf } from "../../services/http";
import type { GroupAdmin, Paged, Product } from "../../types";
import { formatDate, formatPrice, toBn } from "../../utils/format";

const PAGE_SIZE = 10;
type Tab = "products" | "groups";

export default function AdminContent() {
  const [tab, setTab] = useState<Tab>("products");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [products, setProducts] = useState<Paged<Product> | null>(null);
  const [groups, setGroups] = useState<Paged<GroupAdmin> | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const load = useCallback(() => {
    const params = { q: search, offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    const request = tab === "products" ? listAdminProducts(params).then(setProducts) : listAdminGroups(params).then(setGroups);
    request.catch((e) => setError(messageOf(e)));
  }, [tab, search, page]);
  useEffect(load, [load]);

  function switchTab(next: Tab) {
    setTab(next);
    setPage(1);
    setSelected(new Set());
    setQ("");
    setSearch("");
  }

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function removeSelected(ids: number[]) {
    if (ids.length === 0 || !window.confirm(`${toBn(ids.length)}টি ${tab === "products" ? "পণ্য" : "গ্রুপ"} মুছে ফেলবেন?`)) return;
    try {
      const result = tab === "products" ? await bulkDeleteProducts(ids) : await bulkDeleteGroups(ids);
      setError("");
      setFlash(`${toBn(result.deleted)}টি মুছে ফেলা হয়েছে`);
      setSelected(new Set());
      load();
    } catch (e) {
      setFlash("");
      setError(messageOf(e));
    }
  }

  const items = tab === "products" ? products : groups;
  const ids = (tab === "products" ? products?.items : groups?.items)?.map((i) => i.id) ?? [];

  return (
    <>
      <nav className="subnav small-nav" aria-label="কনটেন্টের ধরন">
        <button type="button" className={tab === "products" ? "active" : ""} onClick={() => switchTab("products")}>পণ্য</button>
        <button type="button" className={tab === "groups" ? "active" : ""} onClick={() => switchTab("groups")}>গ্রুপ</button>
      </nav>
      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="card filters">
        <form onSubmit={(e: FormEvent) => { e.preventDefault(); setPage(1); setSearch(q.trim()); }} className="search">
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="নাম খুঁজুন" aria-label="খুঁজুন" />
          <button type="submit" className="btn">খুঁজুন</button>
        </form>
      </div>

      <div className="toolbar">
        <span className="muted">নির্বাচিত: {toBn(selected.size)}</span>
        <button type="button" className="btn btn-danger" disabled={selected.size === 0} onClick={() => removeSelected([...selected])}>
          নির্বাচিত মুছুন
        </button>
        {tab === "products" && (
          <button type="button" className="btn push" onClick={() => downloadCsv("products", { q: search }).catch((e) => setError(messageOf(e)))}>
            CSV ডাউনলোড
          </button>
        )}
      </div>

      {items === null && !error ? (
        <p className="muted">লোড হচ্ছে...</p>
      ) : items && items.items.length === 0 ? (
        <div className="card empty"><p>কিছু পাওয়া যায়নি।</p></div>
      ) : (
        items && (
          <>
            <p className="muted">মোট {toBn(items.total)}টি</p>
            <div className="card table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>
                      <input type="checkbox" aria-label="সব বাছুন" checked={ids.length > 0 && ids.every((i) => selected.has(i))}
                        onChange={(e) => setSelected(e.target.checked ? new Set(ids) : new Set())} />
                    </th>
                    {tab === "products" ? (<><th>পণ্য</th><th>দাম</th><th>বিক্রেতা</th><th>গ্রুপ</th></>) : (<><th>গ্রুপ</th><th>owner</th><th>সদস্য</th><th>পণ্য</th><th>তৈরি</th></>)}
                    <th><span className="sr-only">কাজ</span></th>
                  </tr>
                </thead>
                <tbody>
                  {tab === "products"
                    ? products?.items.map((p) => (
                        <tr key={p.id}>
                          <td><input type="checkbox" aria-label={`${p.name_bn} বাছুন`} checked={selected.has(p.id)} onChange={() => toggle(p.id)} /></td>
                          <td><Link to={`/products/${p.id}`}>{p.name_bn}</Link></td>
                          <td>{formatPrice(p.price)}</td>
                          <td>{p.owner_name ?? "Supply Mart"}</td>
                          <td>{p.group_name ?? "—"}</td>
                          <td className="row-actions"><button type="button" className="link-danger" onClick={() => removeSelected([p.id])}>মুছুন</button></td>
                        </tr>
                      ))
                    : groups?.items.map((g) => (
                        <tr key={g.id}>
                          <td><input type="checkbox" aria-label={`${g.name} বাছুন`} checked={selected.has(g.id)} onChange={() => toggle(g.id)} /></td>
                          <td>{g.name}</td>
                          <td><Link to={`/admin/users/${g.owner_id}`}>{g.owner_name}</Link></td>
                          <td>{toBn(g.member_count)}</td>
                          <td>{toBn(g.product_count)}</td>
                          <td>{formatDate(g.created_at)}</td>
                          <td className="row-actions"><button type="button" className="link-danger" onClick={() => removeSelected([g.id])}>মুছুন</button></td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={items.total} onChange={setPage} />
          </>
        )
      )}
    </>
  );
}
