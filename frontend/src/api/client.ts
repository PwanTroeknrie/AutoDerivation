import type {
  RootAnalysis,
  GeneratePayload,
  GenerateResult,
  ValidatePayload,
  EtymologyResult,
  Options,
  RuntimeConfig,
  RuntimeConfigPayload,
  WarmupResult,
} from "../types";

const BASE = "/api";

async function postJson<T>(url: string, payload: Record<string, unknown>): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function generateRoots(payload: GeneratePayload): Promise<GenerateResult> {
  return postJson<GenerateResult>(`${BASE}/generate`, payload as unknown as Record<string, unknown>);
}

export async function validateRoot(payload: ValidatePayload): Promise<RootAnalysis> {
  return postJson<RootAnalysis>(`${BASE}/validate`, payload as unknown as Record<string, unknown>);
}

export async function analyzeEtymology(concept: string): Promise<EtymologyResult> {
  return postJson<EtymologyResult>(`${BASE}/etymology`, { concept });
}

export async function fetchRuntimeConfig(): Promise<RuntimeConfig> {
  const res = await fetch(`${BASE}/config`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json() as Promise<RuntimeConfig>;
}

export async function saveRuntimeConfig(payload: RuntimeConfigPayload): Promise<RuntimeConfig> {
  return postJson<RuntimeConfig>(`${BASE}/config`, payload as unknown as Record<string, unknown>);
}

export async function warmupEtymology(preloadModel = false): Promise<WarmupResult> {
  return postJson<WarmupResult>(`${BASE}/etymology/warmup`, { preload_model: preloadModel });
}

export async function fetchOptions(): Promise<Options> {
  const res = await fetch(`${BASE}/options`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json() as Promise<Options>;
}
