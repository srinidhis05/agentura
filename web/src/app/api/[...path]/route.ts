import { NextRequest, NextResponse } from "next/server";

const API_TARGET = process.env.API_TARGET || "http://localhost:3001";

/**
 * Catch-all API proxy that replaces next.config.ts rewrites.
 * Next.js rewrite proxy has a ~30s timeout that kills long-running
 * skill executions. This route handler gives us explicit timeout control.
 */
async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const search = req.nextUrl.search;
  const url = `${API_TARGET}${path}${search}`;

  const isSSE = path.includes("/execute-stream");
  const isPipeline = path.includes("/pipelines/") && path.includes("/execute");
  const isExecute = path.includes("/execute");
  const timeoutMs = isPipeline || isSSE ? 600_000 : isExecute ? 120_000 : 30_000;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const headers = new Headers();
    headers.set("Content-Type", req.headers.get("Content-Type") || "application/json");

    const resp = await fetch(url, {
      method: req.method,
      headers,
      body: req.method !== "GET" && req.method !== "HEAD" ? await req.blob() : undefined,
      signal: controller.signal,
    });

    const body = await resp.arrayBuffer();

    return new NextResponse(body, {
      status: resp.status,
      headers: {
        "Content-Type": resp.headers.get("Content-Type") || "application/json",
      },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return NextResponse.json(
        { error: "Gateway timeout — skill execution took too long" },
        { status: 504 },
      );
    }
    return NextResponse.json(
      { error: `Gateway unreachable: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 },
    );
  } finally {
    clearTimeout(timer);
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;

export const maxDuration = 300;
