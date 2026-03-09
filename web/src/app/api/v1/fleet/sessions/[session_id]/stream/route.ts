import { NextRequest } from "next/server";

const API_TARGET = process.env.API_TARGET || "http://localhost:3001";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ session_id: string }> },
) {
  const { session_id } = await params;
  const url = `${API_TARGET}/api/v1/fleet/sessions/${encodeURIComponent(session_id)}/stream`;

  const resp = await fetch(url, {
    headers: { Accept: "text/event-stream" },
  });

  if (!resp.ok || !resp.body) {
    return new Response(await resp.text(), { status: resp.status });
  }

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
