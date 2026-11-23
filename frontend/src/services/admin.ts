import type {
  Activity, AdminStats, AdminUser, GroupAdmin, Paged, Product, SecurityOverview, UserDetail,
} from "../types";
import { body, json, paged, query, request } from "./http";

type Params = Record<string, string | number | boolean | undefined | null>;

export const getStats = (): Promise<AdminStats> => json("/admin/stats");

export const listUsers = (p: Params): Promise<Paged<AdminUser>> => paged(`/admin/users${query(p)}`);
export const getUserDetail = (id: number): Promise<UserDetail> => json(`/admin/users/${id}`);

export const banUser = (id: number, reason: string): Promise<AdminUser> =>
  json(`/admin/users/${id}/ban`, { method: "POST", body: body({ reason }) });
export const unbanUser = (id: number): Promise<AdminUser> => json(`/admin/users/${id}/unban`, { method: "POST" });
export const changeRole = (id: number, role: "user" | "admin"): Promise<AdminUser> =>
  json(`/admin/users/${id}/role`, { method: "PATCH", body: body({ role }) });
export const revokeUserSessions = (id: number): Promise<{ revoked: number }> =>
  json(`/admin/users/${id}/revoke-sessions`, { method: "POST" });

export interface BulkResult {
  done: number[];
  skipped: { id: number; reason: string }[];
}
export const bulkUsers = (action: "ban" | "unban", ids: number[], reason?: string): Promise<BulkResult> =>
  json("/admin/users/bulk", { method: "POST", body: body({ action, ids, reason }) });

export const listAdminProducts = (p: Params): Promise<Paged<Product>> => paged(`/admin/products${query(p)}`);
export const bulkDeleteProducts = (ids: number[]): Promise<{ deleted: number }> =>
  json("/admin/products/bulk-delete", { method: "POST", body: body({ ids }) });

export const listAdminGroups = (p: Params): Promise<Paged<GroupAdmin>> => paged(`/admin/groups${query(p)}`);
export const bulkDeleteGroups = (ids: number[]): Promise<{ deleted: number }> =>
  json("/admin/groups/bulk-delete", { method: "POST", body: body({ ids }) });

export const listActivity = (p: Params): Promise<Paged<Activity>> => paged(`/admin/activity${query(p)}`);
export const getSecurity = (days: number): Promise<SecurityOverview> => json(`/admin/security${query({ days })}`);

// CSV: header-এ token লাগে, তাই সাধারণ লিংক না, fetch করে ফাইল নামাই
export async function downloadCsv(kind: "users" | "products" | "activity", p: Params): Promise<void> {
  const res = await request(`/admin/export/${kind}${query(p)}`);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = `${kind}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
