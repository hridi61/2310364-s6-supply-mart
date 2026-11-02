export type Unit = "kg" | "litre" | "dozen" | "piece";

export interface Category {
  id: number;
  slug: string;
  name_bn: string;
  icon: string;
}

export interface Product {
  id: number;
  name_bn: string;
  category_id: number;
  category_slug: string;
  category_name_bn: string;
  unit: Unit;
  price: number;
  stock: number;
  icon: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// নতুন পণ্য বানানোর সময় যা পাঠাতে হয় (POST /products)
export interface ProductInput {
  name_bn: string;
  category_id: number;
  unit: Unit;
  price: number;
  stock: number;
  icon?: string | null;
}

// বদলানোর সময় যে ঘরগুলো পাঠানো হয় (PATCH /products/{id})
export type ProductPatch = Partial<ProductInput> & { is_active?: boolean };

export type SortOption = "" | "price_asc" | "price_desc";

export interface ProductQuery {
  category?: string;
  q?: string;
  sort?: SortOption;
  offset?: number;
  limit?: number;
}

export interface ProductPage {
  items: Product[];
  total: number;
}