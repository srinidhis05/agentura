import { NextRequest } from "next/server";

const API_TARGET = process.env.API_TARGET || "http://localhost:3001";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const url = `${API_TARGET}/api/v1/pipelines/${encodeURIComponent(name)}/execute-stream`;

  const body = await req.arrayBuffer();

  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!resp.ok || !resp.body) {
    return new Response(await resp.text(), { status: resp.status });
  }

  // Pipe upstream chunks to the client via a pull-based ReadableStream
  const reader = resp.body.getReader();
  const stream = new ReadableStream({
    async pull(controller) {
      const { done, value } = await reader.read();
      if (done) {
        controller.close();
        return;
      }
      controller.enqueue(value);
    },
    cancel() {
      reader.cancel();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
