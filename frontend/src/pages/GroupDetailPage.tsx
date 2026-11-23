import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Alert from "../components/Alert";
import PermChecks from "../components/PermChecks";
import { listGroupProducts } from "../services/api";
import { messageOf } from "../services/http";
import * as groupsApi from "../services/groups";
import type { GroupDetail, GroupPerm, Product } from "../types";
import { PERM_LABEL, formatPrice, toBn } from "../utils/format";
import NotFoundPage from "./NotFoundPage";

export default function GroupDetailPage() {
  const { id } = useParams();
  const groupId = Number(id);
  const navigate = useNavigate();
  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");
  const [newName, setNewName] = useState("");
  const [email, setEmail] = useState("");
  const [perms, setPerms] = useState<GroupPerm[]>([]);

  const load = useCallback(() => {
    groupsApi
      .getGroup(groupId)
      .then((g) => {
        setGroup(g);
        setNewName(g.name);
      })
      .catch((e) => {
        if (e?.status === 404) setNotFound(true);
        else setError(messageOf(e));
      });
    listGroupProducts(groupId)
      .then((p) => setProducts(p.items))
      .catch(() => setProducts([]));
  }, [groupId]);
  useEffect(load, [load]);

  async function run(action: () => Promise<unknown>, okText: string) {
    try {
      await action();
      setError("");
      setFlash(okText);
      load();
    } catch (e) {
      setFlash("");
      setError(messageOf(e));
    }
  }

  function addMember(e: FormEvent) {
    e.preventDefault();
    run(async () => {
      await groupsApi.addMember(groupId, email.trim(), perms);
      setEmail("");
      setPerms([]);
    }, "সদস্য যোগ হয়েছে");
  }

  async function removeGroup() {
    if (!group || !window.confirm(`গ্রুপ "${group.name}" মুছে ফেলবেন? পণ্যগুলো থাকবে, শুধু গ্রুপ থেকে আলাদা হবে।`)) return;
    try {
      await groupsApi.deleteGroup(groupId);
      navigate("/groups", { replace: true });
    } catch (e) {
      setError(messageOf(e));
    }
  }

  if (notFound) return <NotFoundPage />;
  if (!group) return error ? <Alert kind="error">{error}</Alert> : <p className="muted">লোড হচ্ছে...</p>;

  const owner = group.is_owner;
  const canCreate = group.my_permissions.includes("create");

  return (
    <>
      <p>
        <Link to="/groups">← আমার গ্রুপ</Link>
      </p>
      <div className="page-head">
        <div>
          <h1>{group.name}</h1>
          <p className="muted">
            owner: {group.owner_name} · আমার অনুমতি:{" "}
            {owner ? "সব" : group.my_permissions.length ? group.my_permissions.map((p) => PERM_LABEL[p]).join(", ") : "শুধু দেখা"}
          </p>
        </div>
        {owner && (
          <button type="button" className="btn btn-danger" onClick={removeGroup}>
            গ্রুপ মুছুন
          </button>
        )}
      </div>

      {flash && <Alert kind="success">{flash}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      {owner && (
        <form
          className="card inline-form"
          onSubmit={(e) => {
            e.preventDefault();
            run(() => groupsApi.renameGroup(groupId, newName.trim()), "নাম বদলেছে");
          }}
        >
          <label htmlFor="rename">গ্রুপের নাম বদলান</label>
          <input id="rename" value={newName} onChange={(e) => setNewName(e.target.value)} maxLength={60} />
          <button type="submit" className="btn" disabled={newName.trim().length < 2 || newName === group.name}>
            নাম বদলান
          </button>
        </form>
      )}

      <h2 className="section">সদস্য ও অনুমতি</h2>
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>সদস্য</th>
              <th>অনুমতি</th>
              <th>
                <span className="sr-only">কাজ</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {group.members.map((m) => (
              <tr key={m.user_id}>
                <td>
                  {m.name} <span className="muted small">{m.email}</span> {m.is_owner && <span className="badge badge-on">owner</span>}
                </td>
                <td>
                  {m.is_owner ? (
                    <span className="muted">সব অনুমতি</span>
                  ) : (
                    <PermChecks
                      value={m.permissions}
                      disabled={!owner}
                      onChange={(v) => run(() => groupsApi.setMemberPermissions(groupId, m.user_id, v), "অনুমতি বদলেছে")}
                    />
                  )}
                </td>
                <td className="row-actions">
                  {owner && !m.is_owner && (
                    <button type="button" className="link-danger" onClick={() => run(() => groupsApi.removeMember(groupId, m.user_id), "সদস্য সরানো হয়েছে")}>
                      সরান
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!owner && <p className="muted small">সদস্য যোগ, অনুমতি বদল, নাম বদল ও গ্রুপ মোছা শুধু owner করতে পারেন।</p>}

      {owner && (
        <form onSubmit={addMember} className="card form">
          <h3>সদস্য যোগ করুন</h3>
          <div className="field">
            <label htmlFor="memail">সদস্যের ইমেইল (আগে থেকে সাইন আপ করা থাকতে হবে)</label>
            <input id="memail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <PermChecks value={perms} onChange={setPerms} />
          <button type="submit" className="btn btn-primary" disabled={!email.trim()}>
            যোগ করুন
          </button>
        </form>
      )}

      <div className="page-head section">
        <h2>গ্রুপের পণ্য ({toBn(products.length)})</h2>
        {canCreate && (
          <Link to={`/products/new?group=${group.id}`} className="btn btn-primary">
            + গ্রুপে পণ্য যোগ
          </Link>
        )}
      </div>
      {products.length === 0 ? (
        <p className="muted">এই গ্রুপে এখনো কোনো পণ্য নেই।</p>
      ) : (
        <div className="card table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>পণ্য</th>
                <th>দাম</th>
                <th>স্টক</th>
                <th>যোগ করেছেন</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td>
                    <span aria-hidden>{p.icon}</span> <Link to={`/products/${p.id}`}>{p.name_bn}</Link>
                  </td>
                  <td>{formatPrice(p.price)}</td>
                  <td>{toBn(p.stock)}</td>
                  <td>{p.owner_name ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
