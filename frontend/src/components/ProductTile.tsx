import { Link } from "react-router-dom";
import type { Product } from "../types";
import { UNIT_LABEL, formatPrice } from "../utils/format";

export default function ProductTile({ product }: { product: Product }) {
  const out = product.stock <= 0;
  return (
    <article className={`hm-tile${out ? " hm-tile-out" : ""}`}>
      <div className="hm-tile-art" aria-hidden>
        {product.icon}
      </div>
      <p className="hm-tile-cat">{product.category_name_bn}</p>
      <h3 className="hm-tile-name">{product.name_bn}</h3>
      <p className="hm-tile-price">
        {formatPrice(product.price)} <span>/ {UNIT_LABEL[product.unit]}</span>
      </p>
      <p className={out ? "hm-stock hm-stock-out" : "hm-stock"}>{out ? "স্টক নেই" : "স্টকে আছে"}</p>
      <Link to={`/products/${product.id}`} className="hm-tile-btn">
        বিস্তারিত দেখুন
      </Link>
    </article>
  );
}
