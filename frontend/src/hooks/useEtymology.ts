import { useState, useCallback } from "react";
import { analyzeEtymology } from "../api/client";
import type { EtymologyResult } from "../types";

export function useEtymology() {
  const [result, setResult] = useState<EtymologyResult | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (concept: string) => {
    setStatus("loading");
    setError(null);
    try {
      const data = await analyzeEtymology(concept);
      setResult(data);
      setStatus("idle");
      return data;
    } catch (e) {
      setStatus("error");
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      return null;
    }
  }, []);

  return { result, status, error, analyze, setResult };
}
