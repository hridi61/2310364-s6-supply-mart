import { Link } from "react-router-dom";
import type { Category } from "../types";

// ক্যাটাগরির গোল আইকনের সারি: চাপলে ওই ক্যাটাগরির পণ্যের তালিকা খোলে
export default function CategoryTiles({ categories }: { categories: Category[] }) {
  return (
    <ul className="hm-cats">
      {categories.map((c) => (
        <li key={c.id}>
          <Link to={`/products?category=${encodeURIComponent(c.slug)}`} className="hm-cat">
            <span className="hm-cat-icon" aria-hidden>
              {c.icon}
            </span>
            <span>{c.name_bn}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
