import type {
  Category,
  Product,
  ProductInput,
  ProductPage,
  ProductPatch,
  ProductQuery,
} from "../types";

// Vite dev server /api কে backend-এ (port 8000) পাঠায়; Vercel-এও একই origin
const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  fields: Record<string, string>;

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

// সার্ভারের এরর body থেকে বার্তা আর কোন ঘরে ভুল সেটা বের করে
async function toApiError(res: Response): Promise<ApiError> {
  let message = `অনুরোধ ব্যর্থ হয়েছে (${res.status})`;
  const fields: Record<string, string> = {};

  try {
    const data = await res.json();
    const detail = data?.detail;
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      for (const item of detail) {
        const loc: unknown[] = item.loc ?? [];
        const field = String(loc[loc.length - 1] ?? "");
        if (field) fields[field] = String(item.msg);
      }
      message = "ইনপুটে ভুল আছে, লাল চিহ্নিত ঘরগুলো দেখুন";
    }
  } catch {
    // body JSON না হলে ডিফল্ট বার্তাই থাকবে
  }

  return new ApiError(res.status, message, fields);
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না। ব্যাকএন্ড চালু আছে কিনা দেখুন");
  }
  if (!res.ok) throw await toApiError(res);
  return res;
}

function toQueryString(query: ProductQuery): string {
  const params = new URLSearchParams();
  if (query.category) params.set("category", query.category);
  if (query.q) params.set("q", query.q);
  if (query.sort) params.set("sort", query.sort);
  if (query.offset !== undefined) params.set("offset", String(query.offset));
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  const text = params.toString();
  return text ? `?${text}` : "";
}

// ---- Read list (ক্যাটাগরি) ----
export async function listCategories(): Promise<Category[]> {
  const res = await request("/categories");
  return res.json();
}

// ---- Read list (পণ্য) ----
export async function listProducts(query: ProductQuery = {}): Promise<ProductPage> {
  const res = await request(`/products${toQueryString(query)}`);
  const items: Product[] = await res.json();
  const total = Number(res.headers.get("X-Total-Count") ?? items.length);
  return { items, total };
}

// ---- Read single ----
export async function getProduct(id: number): Promise<Product> {
  const res = await request(`/products/${id}`);
  return res.json();
}

// ---- Create ----
export async function createProduct(input: ProductInput): Promise<Product> {
  const res = await request("/products", { method: "POST", body: JSON.stringify(input) });
  return res.json();
}

// ---- Update ----
export async function updateProduct(id: number, patch: ProductPatch): Promise<Product> {
  const res = await request(`/products/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
  return res.json();
}

// ---- Delete ----
export async function deleteProduct(id: number): Promise<void> {
  await request(`/products/${id}`, { method: "DELETE" });
}