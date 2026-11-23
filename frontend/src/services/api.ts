import type { Category, Product, ProductInput, ProductPage, ProductPatch, ProductQuery } from "../types";
import { body, json, paged, query, request } from "./http";

export { ApiError, messageOf } from "./http";

function toQueryString(q: ProductQuery): string {
  return query({ category: q.category, q: q.q, sort: q.sort, offset: q.offset, limit: q.limit });
}

// ---- Read list (ক্যাটাগরি) ----
export function listCategories(): Promise<Category[]> {
  return json("/categories");
}

// ---- Read list (পণ্য) ----
export function listProducts(q: ProductQuery = {}): Promise<ProductPage> {
  return paged<Product>(`/products${toQueryString(q)}`);
}

export function listGroupProducts(groupId: number): Promise<ProductPage> {
  return paged<Product>(`/products${query({ group_id: groupId, limit: 100 })}`);
}

export function listMyProducts(offset = 0, limit = 8): Promise<ProductPage> {
  return paged<Product>(`/products/mine${query({ offset, limit })}`);
}

// ---- Read single ----
export function getProduct(id: number): Promise<Product> {
  return json(`/products/${id}`);
}

// ---- Create ----
export function createProduct(input: ProductInput): Promise<Product> {
  return json("/products", { method: "POST", body: body(input) });
}

// ---- Update ----
export function updateProduct(id: number, patch: ProductPatch): Promise<Product> {
  return json(`/products/${id}`, { method: "PATCH", body: body(patch) });
}

// ---- Delete ----
export async function deleteProduct(id: number): Promise<void> {
  await request(`/products/${id}`, { method: "DELETE" });
}
