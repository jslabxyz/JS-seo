import { spawn } from "node:child_process";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SCRIPT = path.join(process.cwd(), "py", "js_seo_audit.py");
const WINDOW_MS = 60_000;
const LIMIT = 8;
const hits = new Map<string, number[]>();

type ErrorBody = { ok: false; code: string; error: string };

function clientKey(request: Request) {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return forwarded || "local";
}

function limited(key: string) {
  const now = Date.now();
  const recent = (hits.get(key) || []).filter((time) => now - time < WINDOW_MS);
  if (recent.length >= LIMIT) {
    hits.set(key, recent);
    return true;
  }
  recent.push(now);
  hits.set(key, recent);
  return false;
}

function fail(status: number, code: string, error: string) {
  const body: ErrorBody = { ok: false, code, error };
  return NextResponse.json(body, { status });
}

function runAudit(url: string) {
  return new Promise<{ code: number; stdout: string; stderr: string }>((resolve, reject) => {
    const child = spawn("python3", [SCRIPT, url, "--json", "--timeout", "15"], {
      cwd: path.join(process.cwd(), ".."),
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      signal: AbortSignal.timeout(20_000),
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      if (stdout.length < 1_000_000) stdout += chunk;
    });
    child.stderr.on("data", (chunk: string) => {
      if (stderr.length < 8_000) stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code: code ?? 1, stdout, stderr }));
  });
}

export async function POST(request: Request) {
  if (limited(clientKey(request))) {
    return fail(429, "rate_limit", "Too many checks just now. Wait a minute and try again.");
  }

  let url = "";
  try {
    const body = (await request.json()) as { url?: unknown };
    if (typeof body.url === "string") url = body.url.trim();
  } catch {
    return fail(400, "bad_url", "Enter a public http or https address.");
  }

  if (!url || url.length > 2000 || /[\s\u0000]/.test(url)) {
    return fail(400, "bad_url", "Enter a public http or https address.");
  }

  try {
    const result = await runAudit(url);
    const payload = JSON.parse(result.stdout) as { ok?: boolean; code?: string; error?: string };
    if (!payload || typeof payload !== "object" || typeof payload.ok !== "boolean") {
      return fail(502, "check_failed", "The check did not finish. Try the address again.");
    }
    if (!payload.ok) {
      const status = payload.code === "unsafe_url" || payload.code === "bad_url" ? 400 : 502;
      return NextResponse.json(payload, { status });
    }
    return NextResponse.json(payload);
  } catch {
    return fail(502, "check_failed", "The check did not finish. Try the address again.");
  }
}
