import type { Group, GroupDetail, GroupPerm } from "../types";
import { body, json, request } from "./http";

export const listMyGroups = (): Promise<Group[]> => json("/groups");
export const getGroup = (id: number): Promise<GroupDetail> => json(`/groups/${id}`);

export const createGroup = (name: string, description: string): Promise<Group> =>
  json("/groups", { method: "POST", body: body({ name, description: description || null }) });

export const renameGroup = (id: number, name: string): Promise<Group> =>
  json(`/groups/${id}`, { method: "PATCH", body: body({ name }) });

export async function deleteGroup(id: number): Promise<void> {
  await request(`/groups/${id}`, { method: "DELETE" });
}

export const addMember = (id: number, email: string, permissions: GroupPerm[]): Promise<GroupDetail> =>
  json(`/groups/${id}/members`, { method: "POST", body: body({ email, permissions }) });

export const setMemberPermissions = (id: number, userId: number, permissions: GroupPerm[]): Promise<GroupDetail> =>
  json(`/groups/${id}/members/${userId}`, { method: "PATCH", body: body({ permissions }) });

export async function removeMember(id: number, userId: number): Promise<void> {
  await request(`/groups/${id}/members/${userId}`, { method: "DELETE" });
}
