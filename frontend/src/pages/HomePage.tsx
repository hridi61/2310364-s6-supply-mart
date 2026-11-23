import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Alert from "../components/Alert";
import CategoryTiles from "../components/CategoryTiles";
import ProductTile from "../components/ProductTile";
import { listCategories, listProducts, messageOf } from "../services/api";
import type { Category, Product } from "../types";

export default function HomePage() {
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[] | null>(null);
  const [categoryError, setCategoryError] = useState("");
  const [active, setActive] = useState(""); // নতুন পণ্যের সারির ফিল্টার (ক্যাটাগরির slug)
  const [featured, setFeatured] = useState<Product[] | null>(null);
  const [featuredError, setFeaturedError] = useState("");

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch((e) => setCategoryError(messageOf(e)));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setFeatured(null);
    setFeaturedError("");
    listProducts({ category: active || undefined, limit: 8 })
      .then((page) => !cancelled && setFeatured(page.items))
      .catch((e) => !cancelled && setFeaturedError(messageOf(e)));
    return () => {
      cancelled = true;
    };
  }, [active]);

  return (
    <>
      <section className="hm-hero">
        <div className="hm-hero-text">
          <p className="hm-hero-tag">Supply Mart-এ স্বাগতম</p>
          <h1>
            <span className="hm-hero-accent">মুদির বাজার করুন</span>
            <br />
            আমাদের শপ থেকে।
          </h1>
          <p className="hm-hero-sub">
            চাল, ডাল, তেল, সবজি, মাছ, ডিম ও মসলা: পাড়ার দোকানিদের নিজের পণ্য এক জায়গায়। নিজেও পণ্য তুলুন, আর দোকান-টিম বানিয়ে সদস্যদের আলাদা অনুমতি দিন।
          </p>
          <div className="hm-hero-actions">
            <Link to="/products" className="hm-btn hm-btn-solid">
              পণ্য দেখুন
            </Link>
            {user ? (
              <Link to="/my-products" className="hm-btn">
                আমার পণ্য
              </Link>
            ) : (
              <Link to="/signup" className="hm-btn">
                সাইন আপ করুন
              </Link>
            )}
          </div>
        </div>
        <img src="/supply-hero.png" alt="ফল ও সবজিতে ভরা ঝুড়ি" className="hm-hero-art" width={260} height={240} />
      </section>

      <section className="hm-section" aria-labelledby="cat-title">
        <div className="hm-section-head">
          <h2 id="cat-title">ক্যাটাগরি অনুযায়ী কিনুন</h2>
          <Link to="/categories">সব ক্যাটাগরি ›</Link>
        </div>
        {categoryError && <Alert kind="error">{categoryError}</Alert>}
        {categories === null && !categoryError && <p className="muted">লোড হচ্ছে...</p>}
        {categories && categories.length === 0 && <p className="muted">এখনো কোনো ক্যাটাগরি নেই।</p>}
        {categories && categories.length > 0 && <CategoryTiles categories={categories} />}
      </section>

      <section className="hm-section" aria-labelledby="new-title">
        <div className="hm-section-head">
          <h2 id="new-title">নতুন পণ্য</h2>
          <div className="hm-pills" role="group" aria-label="ক্যাটাগরি বাছুন">
            <button type="button" className={active === "" ? "hm-pill on" : "hm-pill"} onClick={() => setActive("")}>
              সব
            </button>
            {categories?.slice(0, 5).map((c) => (
              <button
                key={c.id}
                type="button"
                className={active === c.slug ? "hm-pill on" : "hm-pill"}
                onClick={() => setActive(c.slug)}
              >
                {c.name_bn}
              </button>
            ))}
          </div>
        </div>
        {featuredError && <Alert kind="error">{featuredError}</Alert>}
        {featured === null && !featuredError && <p className="muted">লোড হচ্ছে...</p>}
        {featured && featured.length === 0 && (
          <div className="card empty">
            <p>এই ক্যাটাগরিতে এখনো কোনো পণ্য নেই।</p>
          </div>
        )}
        {featured && featured.length > 0 && (
          <div className="hm-grid">
            {featured.map((p) => (
              <ProductTile key={p.id} product={p} />
            ))}
          </div>
        )}
        <p className="hm-more">
          <Link to="/products" className="hm-btn hm-btn-solid">
            সব পণ্য দেখুন
          </Link>
        </p>
      </section>
    </>
  );
}
