export interface Sample {
  result: string | null;
  analysis: Record<string, unknown>;
}

export interface RootAnalysis {
  valid: boolean;
  base: string;
  pos: string;
  inflection: string | null;
  subtype: string | null;
  reason: string;
  score: number;
  tokens: string[];
  diagnostics: string[];
  skeleton?: string;
  animacy?: string;
  v_grp?: string;
  sample?: Sample | null;
}

export interface GeneratePayload {
  pos: string | null;
  count: number;
}

export interface GenerateResult {
  roots: RootAnalysis[];
}

export interface ValidatePayload {
  word: string;
  pos: string;
}

export interface EtymologyCandidate {
  w: string;
  d: string;
  s: number;
  source?: string;
  tags?: string[];
}

export interface EtymologyDecision {
  choice: string;
  reason: string;
  comp?: string[];
  source?: string;
  word?: string;
  def?: string;
}

export interface EtymologyResult {
  concept: string;
  decision: EtymologyDecision;
  candidates: EtymologyCandidate[];
  warnings?: string[];
  meta?: {
    ai_mode: string;
    recall_mode: string;
    candidate_count: number;
    elapsed_ms: number;
  };
  error?: string;
}

export interface Options {
  partsOfSpeech: string[];
  counts: number[];
}

export interface RuntimeConfig {
  ai_mode: "cloud" | "local" | "off";
  deepseek: {
    api_key_masked: string;
    base_url: string;
    model: string;
    timeout: number;
    configured: boolean;
  };
  ollama: {
    base_url: string;
    model: string;
    timeout: number;
  };
  paths: {
    db_path: string;
    model_path: string;
    cache_path: string;
  };
  error?: string;
}

export interface RuntimeConfigPayload {
  ai_mode?: "cloud" | "local" | "off";
  deepseek_api_key?: string;
  deepseek_base_url?: string;
  deepseek_model?: string;
  deepseek_timeout?: number;
  ollama_base_url?: string;
  ollama_model?: string;
  ollama_timeout?: number;
  db_path?: string;
  model_path?: string;
  persist?: boolean;
}

export interface WarmupResult {
  ok: boolean;
  collection?: string;
  db_path?: string;
  count?: number;
  elapsed_ms?: number;
  preload_model?: boolean;
  error?: string;
}
