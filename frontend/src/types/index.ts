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
  owner_id: number | null;
  owner_name: string | null;
  group_id: number | null;
  group_name: string | null;
  can_edit: boolean;
  can_delete: boolean;
  can_stock: boolean;
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
  group_id?: number | null;
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

// ---------- ব্যবহারকারী ও session ----------
export type Role = "user" | "admin";

export interface User {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  role: Role;
  is_banned: boolean;
  created_at: string;
  last_login_at: string | null;
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  expires_in: number;
  user: User;
}

export interface SessionInfo {
  id: number;
  ip: string | null;
  user_agent: string | null;
  created_at: string;
  last_used_at: string;
  expires_at: string;
  current: boolean;
}

// ---------- গ্রুপ ----------
export type GroupPerm = "create" | "update" | "stock";

export interface Group {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_name: string;
  member_count: number;
  my_permissions: GroupPerm[];
  is_owner: boolean;
  created_at: string;
}

export interface Member {
  user_id: number;
  name: string;
  email: string;
  permissions: GroupPerm[];
  is_owner: boolean;
}

export interface GroupDetail extends Group {
  members: Member[];
}

// ---------- অ্যাডমিন ----------
export interface AdminUser extends User {
  ban_reason: string | null;
  banned_at: string | null;
  locked_until: string | null;
}

export interface Activity {
  id: number;
  user_id: number | null;
  email: string | null;
  action: string;
  detail: string | null;
  ip: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AdminStats {
  users: number;
  admins: number;
  banned_users: number;
  products: number;
  groups: number;
  new_users_7d: number;
  new_products_7d: number;
  new_groups_7d: number;
  active_sessions: number;
  failed_logins_24h: number;
}

export interface UserDetail {
  user: AdminUser;
  products: { id: number; name_bn: string; price: number; stock: number }[];
  groups: { id: number; name: string; role: string; permissions: string }[];
  sessions: SessionInfo[];
  activity: Activity[];
}

export interface GroupAdmin {
  id: number;
  name: string;
  owner_id: number;
  owner_name: string;
  member_count: number;
  product_count: number;
  created_at: string;
}

export interface SecurityOverview {
  days: number;
  by_ip: { ip: string | null; failures: number; accounts: number }[];
  by_account: { email: string; failures: number; last_at: string }[];
  locked_accounts: { id: number; email: string; locked_until: string }[];
}

export interface Paged<T> {
  items: T[];
  total: number;
}
