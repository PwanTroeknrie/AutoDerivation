import { useState, useCallback } from "react";
import { generateRoots } from "../api/client";
import type { RootAnalysis, GeneratePayload } from "../types";

export function useGenerate() {
  const [roots, setRoots] = useState<RootAnalysis[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async (payload: GeneratePayload) => {
    setStatus("loading");
    setError(null);
    try {
      const data = await generateRoots(payload);
      setRoots(data.roots);
      setStatus("idle");
      return data.roots;
    } catch (e) {
      setStatus("error");
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      return [];
    }
  }, []);

  return { roots, status, error, generate, setRoots };
}
