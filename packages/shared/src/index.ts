export const productName = "Steam Hour Booster Pro";

export const safetyRules = [
  "No anti-detect behavior",
  "No ban bypass or ban evasion",
  "No Steam Guard bypass",
  "No proxy rotation or fingerprint manipulation",
  "Only transparent sessions for user-owned accounts"
] as const;

export type AccountStatus = "offline" | "online" | "error";
export type ActivitySessionStatus = "pending" | "running" | "stopping" | "stopped" | "failed";
