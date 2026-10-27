import apiClient from "@/lib/api";
import type { User } from "@/types";

interface Token {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<Token> {
  const response = await apiClient.post<Token>("/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}

export async function refreshToken(): Promise<Token> {
  const response = await apiClient.post<Token>("/auth/refresh");
  return response.data;
}

export async function changePassword(
  oldPassword: string,
  newPassword: string
): Promise<void> {
  await apiClient.post("/auth/change-password", {
    old_password: oldPassword,
    new_password: newPassword,
  });
}
