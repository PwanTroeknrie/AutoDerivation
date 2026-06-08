import { useEffect, useRef } from "react";
import DecorativeMark from "../components/shared/DecorativeMark";
import Button from "../components/shared/Button";
import PaneHead from "../components/shared/PaneHead";
import EtymologistForm from "../components/etymologist/EtymologistForm";
import DecisionPanel from "../components/etymologist/DecisionPanel";
import GeneratorForm from "../components/generator/GeneratorForm";
import RootGrid from "../components/generator/RootGrid";
import WarmupBadge from "../components/shared/WarmupBadge";
import { useEtymology } from "../hooks/useEtymology";
import { useGenerate } from "../hooks/useGenerate";
import type { WarmupState } from "../App";

interface HeroPageProps {
  warmupState: WarmupState;
}

export default function HeroPage({ warmupState }: HeroPageProps) {
  const toolsRef = useRef<HTMLElement | null>(null);
  const { result: etyResult, status: etyStatus, error: etyError, analyze } = useEtymology();
  const { roots, status: genStatus, error: genError, generate } = useGenerate();

  useEffect(() => {
    generate({ pos: null, count: 8 });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const tools = toolsRef.current;
    if (!tools) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          tools.classList.add("is-visible");
        } else {
          tools.classList.remove("is-visible");
        }
      },
      { threshold: 0.18, rootMargin: "0px 0px -12% 0px" },
    );

    observer.observe(tools);
    return () => observer.disconnect();
  }, []);

  const genStatusText =
    genStatus === "loading" ? "Working" : genStatus === "error" ? "Error" : "Done";

  return (
    <main className="w-[min(1180px,calc(100%-32px))] mx-auto pt-[22px] pb-8 max-[820px]:w-[min(100%-20px,680px)]">
      <section className="hero-motion relative overflow-hidden min-h-[calc(100vh-106px)] grid grid-cols-[minmax(0,1fr)_260px] items-end gap-6 border-b-2 border-ink mb-[18px] pb-6 max-[920px]:min-h-auto max-[920px]:grid-cols-1">
        <div className="hero-signal" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        <div className="hero-orbit" aria-hidden="true" />

        <div className="relative z-[1]">
          <p className="hero-kicker m-0 mb-3 text-[13px] font-extrabold text-blue uppercase tracking-normal">
            AutoDerivation
          </p>
          <h1 className="hero-title m-0 max-w-[900px] text-[clamp(54px,10vw,118px)] leading-[0.94] font-black tracking-normal">
            <span>Etymologist</span>
            <span>+</span>
            <span>Generator</span>
          </h1>
          <p className="hero-copy max-w-[640px] mt-[18px] mb-0 text-lg leading-[1.4]">
            在同一界面完成词源决策、候选审查与新词根生成。
          </p>
          <div className="flex flex-wrap gap-[10px] mt-[22px]">
            <Button as="a" href="/generator">
              Open Workspace
            </Button>
            <Button as="a" href="#tools" variant="ghost">
              Jump To Tools
            </Button>
          </div>
        </div>

        <div className="hero-mark relative z-[1] max-[920px]:w-[188px] max-[920px]:min-h-[150px]">
          <DecorativeMark variant={4} />
        </div>
      </section>

      <section
        ref={toolsRef}
        className="tools-motion relative grid grid-cols-2 gap-4 items-start max-[820px]:grid-cols-1"
        id="tools"
        aria-label="Etymologist and Generator"
      >
        <div className="tools-geo tools-geo-a" aria-hidden="true" />
        <div className="tools-geo tools-geo-b" aria-hidden="true" />

        <div className="tools-panel tools-panel-left panel glass p-[14px]">
          <div className="h-[34px] flex justify-between items-center gap-2 border-b border-ink mb-[14px]">
            <h2 className="text-base m-0 tracking-normal">Etymologist</h2>
            <WarmupBadge state={warmupState} />
          </div>
          <EtymologistForm onSubmit={analyze} loading={etyStatus === "loading"} />

          {etyError && (
            <div className="mt-3 border border-line glass-strong min-h-[178px] p-3 text-bad underline decoration-blue decoration-[3px]">
              {etyError}
            </div>
          )}

          {!etyError && etyResult && <DecisionPanel result={etyResult} />}

          {!etyError && !etyResult && (
            <div className="mt-3 border border-line glass-strong min-h-[178px] p-3 grid place-items-center text-ink/50 text-center">
              Enter a concept to see recall candidates and decision.
            </div>
          )}
        </div>

        <div className="tools-panel tools-panel-right panel glass p-[14px]">
          <PaneHead title="Generator" status={genStatusText} />
          <GeneratorForm onSubmit={generate} loading={genStatus === "loading"} />

          {genError && <div className="mt-3 text-bad">{genError}</div>}

          <div className="mt-3">
            <RootGrid roots={roots} onCardClick={() => {}} />
          </div>
        </div>
      </section>
    </main>
  );
}
