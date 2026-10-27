import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow, parseISO } from "date-fns";

/**
 * Merge Tailwind CSS class names, resolving conflicts.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Base URL for all API requests.  The Vite dev server proxies /api → backend.
 */
export const API_BASE_URL = "/api/v1";

/**
 * Format an ISO date string or Date object as "dd MMM yyyy" (e.g. "15 Oct 2024").
 */
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return "—";
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return format(date, "dd MMM yyyy");
  } catch {
    return String(value);
  }
}

/**
 * Format an ISO date string or Date object as "dd MMM yyyy, HH:mm" (24-hour).
 */
export function formatDateTime(
  value: string | Date | null | undefined
): string {
  if (!value) return "—";
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return format(date, "dd MMM yyyy, HH:mm");
  } catch {
    return String(value);
  }
}

/**
 * Return a human-readable relative time string, e.g. "3 days ago".
 */
export function timeAgo(value: string | Date | null | undefined): string {
  if (!value) return "—";
  try {
    const date = typeof value === "string" ? parseISO(value) : value;
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return String(value);
  }
}

/**
 * Truncate a string to a maximum length, appending "…" when cut.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + "…";
}

/**
 * Convert a plain-text status key like "under_process" → "Under Process".
 */
export function formatStatus(status: string): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
