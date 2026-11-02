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