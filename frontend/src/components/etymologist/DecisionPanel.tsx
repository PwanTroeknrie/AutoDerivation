import CandidateGrid from "./CandidateGrid";
import Chip from "../shared/Chip";
import type { EtymologyResult } from "../../types";

interface DecisionPanelProps {
  result: EtymologyResult;
}

const choiceCopy: Record<string, string> = {
  EXISTED: "Use Existing Root",
  DERIVED: "Derive From Root",
  COMPOUND: "Build Compound",
  GENERATE: "Generate New Root",
};

export default function DecisionPanel({ result }: DecisionPanelProps) {
  const { decision } = result;
  const comp = decision.comp ?? [];

  return (
    <div className="mt-3 border border-line glass-strong min-h-[320px] p-4 grid gap-4">
      <section className="border border-ink bg-white p-4 grid gap-3">
        <div className="flex flex-wrap gap-[6px]">
          <Chip text={`concept: ${result.concept}`} />
          {decision.source && <Chip text={`source: ${decision.source}`} />}
          {result.meta?.ai_mode && <Chip text={`ai: ${result.meta.ai_mode}`} />}
          {typeof result.meta?.elapsed_ms === "number" && <Chip text={`${result.meta.elapsed_ms} ms`} />}
        </div>

        <div className="grid gap-1">
          <p className="m-0 text-[12px] font-extrabold uppercase text-blue">Choice</p>
          <h2 className="m-0 text-[clamp(40px,7vw,82px)] leading-[0.92] font-black text-blue break-words">
            {decision.choice || "UNKNOWN"}
          </h2>
          <p className="m-0 text-[18px] font-extrabold">
            {choiceCopy[decision.choice] ?? "Review Decision"}
          </p>
        </div>
      </section>

      <section className="grid gap-2">
        <p className="m-0 text-[12px] font-extrabold uppercase text-blue">Analysis</p>
        <p className="m-0 text-[18px] leading-[1.45]">
          {decision.reason || "No analysis returned."}
        </p>
      </section>

      <section className="grid gap-2">
        <p className="m-0 text-[12px] font-extrabold uppercase text-blue">Components</p>
        {comp.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(160px,1fr))] gap-[10px]">
            {comp.map((item) => (
              <div key={item} className="border border-ink bg-white p-3">
                <strong className="text-blue text-[24px] leading-none break-words">{item}</strong>
              </div>
            ))}
          </div>
        ) : (
          <div className="border border-line bg-white p-3 text-ink/60">No components selected.</div>
        )}
      </section>

      {result.warnings && result.warnings.length > 0 && (
        <section className="border border-line bg-white p-3 text-sm">
          {result.warnings.map((warning) => (
            <p className="m-0" key={warning}>{warning}</p>
          ))}
        </section>
      )}

      <details className="border border-line bg-white p-3">
        <summary className="cursor-pointer text-[12px] font-extrabold uppercase text-blue">
          Recall Candidates ({result.candidates.length})
        </summary>
        <div className="mt-3">
          <CandidateGrid candidates={result.candidates} />
        </div>
      </details>
    </div>
  );
}
