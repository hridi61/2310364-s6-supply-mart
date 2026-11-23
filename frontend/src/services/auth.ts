import type { SessionInfo, TokenResponse, User } from "../types";
import { body, json, request, setAccessToken } from "./http";

export { refreshSession } from "./http";

export async function login(email: string, password: string): Promise<User> {
  const data = await json<TokenResponse>("/auth/login", { method: "POST", body: body({ email, password }) });
  setAccessToken(data.access_token);
  return data.user;
}

export function signup(email: string, name: string, password: string): Promise<User> {
  return json("/auth/signup", { method: "POST", body: body({ email, name, password }) });
}

export async function logout(): Promise<void> {
  try {
    await request("/auth/logout", { method: "POST" });
  } finally {
    setAccessToken(null);
  }
}

export function updateProfile(data: { name?: string; phone?: string }): Promise<User> {
  return json("/users/me", { method: "PATCH", body: body(data) });
}

export async function changePassword(current_password: string, new_password: string): Promise<void> {
  await request("/users/me/password", { method: "POST", body: body({ current_password, new_password }) });
}

export function listSessions(): Promise<SessionInfo[]> {
  return json("/auth/sessions");
}

export async function revokeSession(id: number): Promise<void> {
  await request(`/auth/sessions/${id}`, { method: "DELETE" });
}
