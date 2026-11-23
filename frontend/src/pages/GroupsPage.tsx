import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import { ApiError, messageOf } from "../services/http";
import { createGroup, listMyGroups } from "../services/groups";
import type { Group } from "../types";
import { PERM_LABEL, toBn } from "../utils/format";

export default function GroupsPage() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState("");

  const load = useCallback(() => {
    listMyGroups()
      .then(setGroups)
      .catch((e) => setError(messageOf(e)));
  }, []);
  useEffect(load, [load]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    try {
      const g = await createGroup(name.trim(), description.trim());
      navigate(`/groups/${g.id}`);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : messageOf(err));
    }
  }

  return (
    <>
      <h1>আমার গ্রুপ</h1>
      <p className="muted">গ্রুপ মানে একটি দোকান-টিম। owner সদস্যদের আলাদা আলাদা অনুমতি দেন।</p>
      {error && <Alert kind="error">{error}</Alert>}

      <div className="grid-2 top">
        <div>
          {groups === null && !error ? (
            <p className="muted">লোড হচ্ছে...</p>
          ) : groups && groups.length === 0 ? (
            <div className="card empty">
              <p className="empty-icon" aria-hidden>
                👥
              </p>
              <p>এখনো কোনো গ্রুপে নেই। ডানের ফর্ম থেকে প্রথম গ্রুপ বানান।</p>
            </div>
          ) : (
            <div className="stack">
              {groups?.map((g) => (
                <Link key={g.id} to={`/groups/${g.id}`} className="card group-card">
                  <strong>{g.name}</strong>
                  <span className="muted small">
                    owner: {g.owner_name} · {toBn(g.member_count)} জন সদস্য
                  </span>
                  <span>
                    {g.is_owner ? (
                      <span className="badge badge-on">owner</span>
                    ) : g.my_permissions.length === 0 ? (
                      <span className="badge">শুধু দেখা</span>
                    ) : (
                      g.my_permissions.map((p) => (
                        <span key={p} className="badge badge-on">
                          {PERM_LABEL[p]}
                        </span>
                      ))
                    )}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <form onSubmit={submit} className="card form" noValidate>
          <h2>নতুন গ্রুপ</h2>
          {formError && <Alert kind="error">{formError}</Alert>}
          <div className="field">
            <label htmlFor="gname">গ্রুপের নাম</label>
            <input id="gname" value={name} onChange={(e) => setName(e.target.value)} maxLength={60} />
          </div>
          <div className="field">
            <label htmlFor="gdesc">বিবরণ (ঐচ্ছিক)</label>
            <input id="gdesc" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={200} />
          </div>
          <button type="submit" className="btn btn-primary" disabled={name.trim().length < 2}>
            গ্রুপ বানান
          </button>
        </form>
      </div>
    </>
  );
}
