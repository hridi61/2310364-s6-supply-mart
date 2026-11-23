import type { Unit } from "../types";

const BN_DIGITS = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"];

// ইংরেজি সংখ্যাকে বাংলা সংখ্যায় বদলায়: 1250 -> ১২৫০
export function toBn(value: number | string): string {
  return String(value).replace(/\d/g, (d) => BN_DIGITS[Number(d)]);
}

export function formatPrice(price: number): string {
  return `৳ ${toBn(price)}`;
}

export const UNITS: Unit[] = ["kg", "litre", "dozen", "piece"];

export const UNIT_LABEL: Record<Unit, string> = {
  kg: "কেজি",
  litre: "লিটার",
  dozen: "ডজন",
  piece: "পিস",
};

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("bn-BD", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Dhaka",
  }).format(new Date(iso));
}

// User-Agent থেকে ছোট নাম: "Chrome · Windows"
export function shortAgent(ua: string | null): string {
  if (!ua) return "অজানা";
  const browser = /Edg\//.test(ua) ? "Edge" : /Chrome\//.test(ua) ? "Chrome" : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : "Browser";
  const os = /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iOS" : /Mac OS/.test(ua) ? "macOS" : /Linux/.test(ua) ? "Linux" : "";
  return os ? `${browser} · ${os}` : browser;
}

export const PERM_LABEL: Record<string, string> = {
  create: "পণ্য যোগ",
  update: "পণ্য সম্পাদনা",
  stock: "শুধু স্টক বদল",
};
