"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { FleetSSEEvent } from "@/lib/api";

export interface AgentState {
  agent_id: string;
  status: string;
  success: boolean;
  cost_usd: number;
  latency_ms: number;
  error_message: string;
}

export function useFleetStream(sessionId: string | null) {
  const [agents, setAgents] = useState<Record<string, AgentState>>({});
  const [sessionDone, setSessionDone] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<string>("");
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const controller = new AbortController();
    abortRef.current = controller;

    const connect = async () => {
      try {
        const resp = await fetch(`/api/v1/fleet/sessions/${sessionId}/stream`, {
          signal: controller.signal,
        });
        if (!resp.ok || !resp.body) return;

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const frames = buffer.split("\n\n");
          buffer = frames.pop()!;

          for (const frame of frames) {
            if (!frame.trim()) continue;
            let eventType = "";
            let dataStr = "";
            for (const line of frame.split("\n")) {
              if (line.startsWith("event: ")) eventType = line.slice(7).trim();
              else if (line.startsWith("data: ")) dataStr = line.slice(6);
            }
            if (!eventType || !dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (eventType === "agent_update") {
                setAgents((prev) => ({
                  ...prev,
                  [data.agent_id]: {
                    agent_id: data.agent_id,
                    status: data.status,
                    success: data.success ?? false,
                    cost_usd: data.cost_usd ?? 0,
                    latency_ms: data.latency_ms ?? 0,
                    error_message: data.error_message ?? "",
                  },
                }));
              } else if (eventType === "session_done") {
                setSessionDone(true);
                setSessionStatus(data.status ?? "completed");
              }
            } catch {
              // skip
            }
          }
        }
      } catch {
        // connection closed or aborted
      }
    };

    connect();
    return () => controller.abort();
  }, [sessionId]);

  return { agents, sessionDone, sessionStatus, stop };
}
