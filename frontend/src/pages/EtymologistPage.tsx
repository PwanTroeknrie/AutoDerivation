import Masthead from "../components/shared/Masthead";
import PaneHead from "../components/shared/PaneHead";
import EtymologistForm from "../components/etymologist/EtymologistForm";
import DecisionPanel from "../components/etymologist/DecisionPanel";
import Chip from "../components/shared/Chip";
import WarmupBadge from "../components/shared/WarmupBadge";
import { useEtymology } from "../hooks/useEtymology";
import type { WarmupState } from "../App";

interface EtymologistPageProps {
  warmupState: WarmupState;
}

export default function EtymologistPage({ warmupState }: EtymologistPageProps) {
  const { result, status, error, analyze } = useEtymology();

  return (
    <main className="w-[min(1180px,calc(100%-32px))] mx-auto py-8 max-[820px]:w-[min(100%-20px,680px)] max-[820px]:pt-[18px]">
      <Masthead eyebrow="AutoDerivation" title="Etymology Decision" markVariant={3} />

      {error && <div className="text-bad underline decoration-blue decoration-[3px] mb-4">{error}</div>}

      <section className="grid grid-cols-[minmax(0,1.65fr)_minmax(280px,0.75fr)] gap-4 max-[920px]:grid-cols-1">
        <section className="panel glass p-[14px]">
          <div className="h-[34px] flex justify-between items-center gap-2 border-b border-ink mb-[14px]">
            <h2 className="text-base m-0 tracking-normal">Etymologist</h2>
            <WarmupBadge state={warmupState} />
          </div>
          <EtymologistForm onSubmit={analyze} loading={status === "loading"} />

          {error && (
            <div className="mt-3 border border-line glass-strong min-h-[178px] p-3 text-bad underline decoration-blue decoration-[3px]">
              {error}
            </div>
          )}

          {!error && result && (
            <DecisionPanel result={result} />
          )}

          {!error && !result && (
            <div className="mt-3 border border-line glass-strong min-h-[178px] p-3 grid place-items-center text-ink/50 text-center">
              Enter a concept to see recall candidates and decision.
            </div>
          )}
        </section>

        <section className="panel glass p-4">
          <PaneHead title="Decision Model" status="Info" />
          <div className="grid gap-3 text-sm leading-relaxed">
            <p>
              The etymologist first recalls related roots, then chooses whether the concept already exists,
              can be derived, can be compounded, or needs a new generated root.
            </p>
            <div className="flex flex-wrap gap-[6px]">
              <Chip text="EXISTED" />
              <Chip text="DERIVED" />
              <Chip text="COMPOUND" />
              <Chip text="GENERATE" />
            </div>
            <p className="text-ink/60 text-xs mt-2">
              If vector search, local LLM, or cloud AI is unavailable, the API now returns a rule-based
              fallback with warnings instead of failing the page.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}
