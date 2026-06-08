import { useEffect, useState, type FormEvent } from "react";
import Masthead from "../components/shared/Masthead";
import PaneHead from "../components/shared/PaneHead";
import Field from "../components/shared/Field";
import Button from "../components/shared/Button";
import Chip from "../components/shared/Chip";
import { fetchRuntimeConfig, saveRuntimeConfig, warmupEtymology } from "../api/client";
import type { RuntimeConfig, RuntimeConfigPayload, WarmupResult } from "../types";

export default function SettingsPage() {
  const [config, setConfig] = useState<RuntimeConfig | null>(null);
  const [status, setStatus] = useState("Loading");
  const [warmup, setWarmup] = useState<WarmupResult | null>(null);

  useEffect(() => {
    fetchRuntimeConfig()
      .then((data) => {
        setConfig(data);
        setStatus("Ready");
      })
      .catch((error) => setStatus(error instanceof Error ? error.message : String(error)));
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload: RuntimeConfigPayload = {
      ai_mode: form.get("ai_mode") as RuntimeConfigPayload["ai_mode"],
      deepseek_api_key: String(form.get("deepseek_api_key") || "").trim(),
      deepseek_base_url: String(form.get("deepseek_base_url") || "").trim(),
      deepseek_model: String(form.get("deepseek_model") || "").trim(),
      deepseek_timeout: Number(form.get("deepseek_timeout") || 30),
      ollama_base_url: String(form.get("ollama_base_url") || "").trim(),
      ollama_model: String(form.get("ollama_model") || "").trim(),
      ollama_timeout: Number(form.get("ollama_timeout") || 120),
      db_path: String(form.get("db_path") || "").trim(),
      model_path: String(form.get("model_path") || "").trim(),
      persist: true,
    };
    if (!payload.deepseek_api_key) delete payload.deepseek_api_key;
    setStatus("Saving");
    const next = await saveRuntimeConfig(payload);
    setConfig(next);
    setStatus("Saved");
  };

  const doWarmup = async (preloadModel: boolean) => {
    setStatus(preloadModel ? "Preloading model" : "Warming ChromaDB");
    const result = await warmupEtymology(preloadModel);
    setWarmup(result);
    setStatus(result.ok ? "Warm" : "Warmup failed");
  };

  return (
    <main className="w-[min(1180px,calc(100%-32px))] mx-auto py-8 max-[820px]:w-[min(100%-20px,680px)]">
      <Masthead eyebrow="Runtime" title="Settings" markVariant={3} />

      <section className="grid grid-cols-[minmax(0,1.35fr)_minmax(280px,0.8fr)] gap-4 max-[920px]:grid-cols-1">
        <form
          key={config ? JSON.stringify(config) : "loading"}
          onSubmit={submit}
          className="panel glass p-4 grid gap-4"
        >
          <PaneHead title="AI Configuration" status={status} />

          <div className="grid grid-cols-3 gap-3 max-[820px]:grid-cols-1">
            <Field label="Mode" htmlFor="ai_mode">
              <select id="ai_mode" name="ai_mode" defaultValue={config?.ai_mode ?? "local"} className="input-brutal">
                <option value="cloud">DeepSeek Cloud</option>
                <option value="local">Local Ollama</option>
                <option value="off">Rules Only</option>
              </select>
            </Field>
            <Field label="DeepSeek Model" htmlFor="deepseek_model">
              <input id="deepseek_model" name="deepseek_model" className="input-brutal" defaultValue={config?.deepseek.model ?? "deepseek-chat"} />
            </Field>
            <Field label="DeepSeek Timeout" htmlFor="deepseek_timeout">
              <input id="deepseek_timeout" name="deepseek_timeout" type="number" className="input-brutal" defaultValue={config?.deepseek.timeout ?? 30} />
            </Field>
          </div>

          <Field label="DeepSeek API Key" htmlFor="deepseek_api_key">
            <input id="deepseek_api_key" name="deepseek_api_key" type="password" className="input-brutal" placeholder={config?.deepseek.api_key_masked || "sk-..."} />
          </Field>

          <Field label="DeepSeek Base URL" htmlFor="deepseek_base_url">
            <input id="deepseek_base_url" name="deepseek_base_url" className="input-brutal" defaultValue={config?.deepseek.base_url ?? "https://api.deepseek.com/v1"} />
          </Field>

          <div className="grid grid-cols-[1fr_160px] gap-3 max-[820px]:grid-cols-1">
            <Field label="Ollama Base URL" htmlFor="ollama_base_url">
              <input id="ollama_base_url" name="ollama_base_url" className="input-brutal" defaultValue={config?.ollama.base_url ?? "http://localhost:11434/api/chat"} />
            </Field>
            <Field label="Ollama Timeout" htmlFor="ollama_timeout">
              <input id="ollama_timeout" name="ollama_timeout" type="number" className="input-brutal" defaultValue={config?.ollama.timeout ?? 120} />
            </Field>
          </div>

          <Field label="Ollama Model" htmlFor="ollama_model">
            <input id="ollama_model" name="ollama_model" className="input-brutal" defaultValue={config?.ollama.model ?? ""} />
          </Field>

          <Field label="ChromaDB Path" htmlFor="db_path">
            <input id="db_path" name="db_path" className="input-brutal" defaultValue={config?.paths.db_path ?? ""} />
          </Field>

          <Field label="Embedding Model Path" htmlFor="model_path">
            <input id="model_path" name="model_path" className="input-brutal" defaultValue={config?.paths.model_path ?? ""} />
          </Field>

          <div className="flex flex-wrap gap-2">
            <Button type="submit">Save Runtime Config</Button>
            <Button type="button" variant="ghost" onClick={() => doWarmup(false)}>Warm ChromaDB</Button>
            <Button type="button" variant="ghost" onClick={() => doWarmup(true)}>Preload Model</Button>
          </div>
        </form>

        <aside className="panel glass p-4 grid gap-4 content-start">
          <PaneHead title="Environment" status="Live" />
          <div className="flex flex-wrap gap-[6px]">
            <Chip text={`mode: ${config?.ai_mode ?? "-"}`} />
            <Chip text={`deepseek: ${config?.deepseek.configured ? "configured" : "missing"}`} />
            <Chip text={`key: ${config?.deepseek.api_key_masked || "none"}`} />
          </div>
          <div className="border border-line bg-white p-3 text-sm break-words">
            <strong className="text-blue">Cache</strong>
            <p className="m-0 mt-2">{config?.paths.cache_path ?? "-"}</p>
          </div>
          {warmup && (
            <div className="border border-line bg-white p-3 text-sm break-words">
              <strong className="text-blue">Warmup</strong>
              <p className="m-0 mt-2">{warmup.ok ? "Ready" : "Failed"} · {warmup.elapsed_ms ?? 0} ms</p>
              <p className="m-0">{warmup.collection ?? "-"}</p>
              {typeof warmup.count === "number" && <p className="m-0">items: {warmup.count}</p>}
              {warmup.error && <p className="m-0 text-bad">{warmup.error}</p>}
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}
