export type CheckStatus = "fix" | "review" | "clear";

export type Check = {
  id: string;
  group: string;
  status: CheckStatus;
  label: string;
  detail: string;
};

export type AuditReport = {
  ok: true;
  requested_url: string;
  url: string;
  status_code: number;
  score: number;
  summary: string;
  note: string;
  counts: { fix: number; review: number; clear: number };
  page: {
    title: string;
    title_length: number;
    description: string;
    description_length: number;
    canonical: string;
    robots: string;
    language: string;
    h1: string[];
    h1_count: number;
    word_count: number;
    images: number;
    images_missing_alt: number;
    internal_links: number;
    external_links: number;
    schema_types: string[];
  };
  checks: Check[];
  engine: { name: string; license: string; url: string };
};

export type AuditError = {
  ok: false;
  code: string;
  error: string;
};

export type AuditResponse = AuditReport | AuditError;

export const GROUP_ORDER = ["Index", "Copy", "Images", "Links", "Markup"] as const;

export const STATUS_LABEL: Record<CheckStatus, string> = {
  fix: "Fix",
  review: "Review",
  clear: "Clear",
};
