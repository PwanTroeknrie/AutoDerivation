import { useEffect, useState } from "react";
import Masthead from "../components/shared/Masthead";
import PaneHead from "../components/shared/PaneHead";
import GeneratorForm from "../components/generator/GeneratorForm";
import RootGrid from "../components/generator/RootGrid";
import InspectionPanel from "../components/generator/InspectionPanel";
import ValidateForm from "../components/validate/ValidateForm";
import { useGenerate } from "../hooks/useGenerate";
import { useValidate } from "../hooks/useValidate";
import type { RootAnalysis } from "../types";

export default function GeneratorPage() {
  const { roots, status, error, generate } = useGenerate();
  const { result: validation, status: valStatus, error: valError, validate } = useValidate();
  const [selectedRoot, setSelectedRoot] = useState<RootAnalysis | null>(null);

  // Auto-generate 12 mixed roots on mount
  useEffect(() => {
    generate({ pos: null, count: 12 });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update selected root when new roots come in
  useEffect(() => {
    if (roots.length > 0) {
      setSelectedRoot(roots[0]);
    }
  }, [roots]);

  const handleCardClick = (root: RootAnalysis) => {
    setSelectedRoot(root);
  };

  const genStatusText =
    status === "loading" ? "Generating" : status === "error" ? "Error" : `${roots.length} roots`;

  return (
    <main className="w-[min(1180px,calc(100%-32px))] mx-auto py-8 max-[820px]:w-[min(100%-20px,680px)] max-[820px]:pt-[18px]">
      <Masthead eyebrow="AutoDerivation" title="词根生成与形态合法性检测" markVariant={3} />

      {error && <div className="text-bad underline decoration-blue decoration-[3px] mb-4">{error}</div>}

      <section className="grid grid-cols-2 gap-4 max-[820px]:grid-cols-1">
        {/* Left column: Generate + Results */}
        <div className="flex flex-col gap-4">
          <GeneratorForm onSubmit={generate} loading={status === "loading"} />

          <section className="panel glass min-h-[470px] p-4" aria-live="polite">
            <PaneHead title="生成结果" status={genStatusText} />
            <RootGrid roots={roots} onCardClick={handleCardClick} />
          </section>
        </div>

        {/* Right column: Validate + Inspection */}
        <div className="flex flex-col gap-4">
          <ValidateForm onSubmit={validate} loading={valStatus === "loading"} />

          {valError && <div className="text-bad underline decoration-blue decoration-[3px]">{valError}</div>}

          <section className="panel glass min-h-[470px] p-4">
            <PaneHead title="检测分析" status="Validator" />
            <InspectionPanel root={validation ?? selectedRoot} />
          </section>
        </div>
      </section>
    </main>
  );
}
