import { useState, useCallback } from "react";
import { validateRoot } from "../api/client";
import type { RootAnalysis, ValidatePayload } from "../types";

export function useValidate() {
  const [result, setResult] = useState<RootAnalysis | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(async (payload: ValidatePayload) => {
    setStatus("loading");
    setError(null);
    try {
      const data = await validateRoot(payload);
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

  return { result, status, error, validate, setResult };
}
