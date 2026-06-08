import Chip from "../shared/Chip";
import type { EtymologyDecision } from "../../types";

interface DecisionChipsProps {
  concept: string;
  decision: EtymologyDecision;
  elapsedMs?: number;
}

export default function DecisionChips({ concept, decision, elapsedMs }: DecisionChipsProps) {
  return (
    <div>
      <div className="flex flex-wrap gap-[6px] mb-2">
        <Chip text={`choice: ${decision.choice || "unknown"}`} />
        <Chip text={`concept: ${concept}`} />
        {decision.source && <Chip text={`source: ${decision.source}`} />}
        {typeof elapsedMs === "number" && <Chip text={`${elapsedMs} ms`} />}
      </div>
      <p className="m-0">{decision.reason || "No reason returned."}</p>
      {decision.comp && decision.comp.length > 0 && (
        <div className="flex flex-wrap gap-[6px] mt-2">
          {decision.comp.map((item) => (
            <Chip key={item} text={`comp: ${item}`} />
          ))}
        </div>
      )}
    </div>
  );
}
