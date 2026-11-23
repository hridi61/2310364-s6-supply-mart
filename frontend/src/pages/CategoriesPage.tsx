import { useEffect, useState } from "react";
import Alert from "../components/Alert";
import CategoryTiles from "../components/CategoryTiles";
import { listCategories, messageOf } from "../services/api";
import type { Category } from "../types";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch((e) => setError(messageOf(e)));
  }, []);

  return (
    <>
      <h1>সব ক্যাটাগরি</h1>
      <p className="muted">একটি ক্যাটাগরি বাছুন, ওই ধরনের সব পণ্য দেখাবে।</p>
      {error && <Alert kind="error">{error}</Alert>}
      {categories === null && !error && <p className="muted">লোড হচ্ছে...</p>}
      {categories && categories.length === 0 && <p className="muted">এখনো কোনো ক্যাটাগরি নেই।</p>}
      {categories && categories.length > 0 && <CategoryTiles categories={categories} />}
    </>
  );
}
