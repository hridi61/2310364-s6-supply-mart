import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import type { Category, Product, ProductInput, Unit } from "../types";
import { UNITS, UNIT_LABEL } from "../utils/format";

interface ProductFormProps {
  categories: Category[];
  initial?: Product;
  submitting: boolean;
  submitLabel: string;
  serverErrors: Record<string, string>;
  cancelTo: string;
  onSubmit: (input: ProductInput) => void;
}

// নতুন পণ্য বানানো আর পুরনো পণ্য সম্পাদনা, দুটোতেই এই ফর্ম ব্যবহার হয়
export default function ProductForm({
  categories,
  initial,
  submitting,
  submitLabel,
  serverErrors,
  cancelTo,
  onSubmit,
}: ProductFormProps) {
  const [name, setName] = useState(initial?.name_bn ?? "");
  const [categoryId, setCategoryId] = useState(initial ? String(initial.category_id) : "");
  const [unit, setUnit] = useState<Unit>(initial?.unit ?? "kg");
  const [price, setPrice] = useState(initial ? String(initial.price) : "");
  const [stock, setStock] = useState(initial ? String(initial.stock) : "");
  const [icon, setIcon] = useState(initial?.icon ?? "");
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({});

  const errors = { ...serverErrors, ...clientErrors };

  function validate(): Record<string, string> {
    const found: Record<string, string> = {};
    if (name.trim().length < 2) found.name_bn = "নাম কমপক্ষে ২ অক্ষরের দিন";
    if (!categoryId) found.category_id = "একটি ক্যাটাগরি বেছে নিন";
    const priceNumber = Number(price);
    if (!Number.isInteger(priceNumber) || priceNumber < 1 || priceNumber > 100000) {
      found.price = "দাম ১ থেকে ১,০০,০০০ টাকার মধ্যে পূর্ণ সংখ্যা হতে হবে";
    }
    const stockNumber = Number(stock);
    if (stock === "" || !Number.isInteger(stockNumber) || stockNumber < 0 || stockNumber > 10000) {
      found.stock = "স্টক ০ থেকে ১০,০০০-এর মধ্যে পূর্ণ সংখ্যা হতে হবে";
    }
    return found;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const found = validate();
    setClientErrors(found);
    if (Object.keys(found).length > 0) return;

    onSubmit({
      name_bn: name.trim(),
      category_id: Number(categoryId),
      unit,
      price: Number(price),
      stock: Number(stock),
      icon: icon.trim() === "" ? null : icon.trim(),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="card form" noValidate>
      <div className="field">
        <label htmlFor="name_bn">পণ্যের নাম</label>
        <input
          id="name_bn"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="যেমন: মিনিকেট চাল"
          maxLength={60}
        />
        {errors.name_bn && <p className="error-text">{errors.name_bn}</p>}
      </div>

      <div className="field">
        <label htmlFor="category_id">ক্যাটাগরি</label>
        <select id="category_id" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">বেছে নিন</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.icon} {c.name_bn}
            </option>
          ))}
        </select>
        {errors.category_id && <p className="error-text">{errors.category_id}</p>}
      </div>

      <div className="grid-2">
        <div className="field">
          <label htmlFor="unit">একক</label>
          <select id="unit" value={unit} onChange={(e) => setUnit(e.target.value as Unit)}>
            {UNITS.map((u) => (
              <option key={u} value={u}>
                {UNIT_LABEL[u]}
              </option>
            ))}
          </select>
          {errors.unit && <p className="error-text">{errors.unit}</p>}
        </div>

        <div className="field">
          <label htmlFor="icon">ছবির ইমোজি (ঐচ্ছিক)</label>
          <input id="icon" value={icon} onChange={(e) => setIcon(e.target.value)} placeholder="🍚" maxLength={8} />
          {errors.icon && <p className="error-text">{errors.icon}</p>}
        </div>
      </div>

      <div className="grid-2">
        <div className="field">
          <label htmlFor="price">দাম (টাকা)</label>
          <input
            id="price"
            type="number"
            min={1}
            step={1}
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="72"
          />
          {errors.price && <p className="error-text">{errors.price}</p>}
        </div>

        <div className="field">
          <label htmlFor="stock">স্টক (পরিমাণ)</label>
          <input
            id="stock"
            type="number"
            min={0}
            step={1}
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            placeholder="100"
          />
          {errors.stock && <p className="error-text">{errors.stock}</p>}
        </div>
      </div>

      <div className="actions">
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "জমা হচ্ছে..." : submitLabel}
        </button>
        <Link to={cancelTo} className="btn">
          বাতিল
        </Link>
      </div>
    </form>
  );
}