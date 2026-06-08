import Chip from "../shared/Chip";
import type { EtymologyCandidate } from "../../types";

interface CandidateCardProps {
  candidate: EtymologyCandidate;
}

export default function CandidateCard({ candidate }: CandidateCardProps) {
  return (
    <div className="border border-line bg-white/80 p-2 grid gap-[6px] min-h-[118px]">
      <strong className="text-blue break-words">
        {candidate.w || "-"}
      </strong>
      <div className="text-sm leading-snug break-words">{candidate.d || "-"}</div>
      <div className="flex flex-wrap gap-[6px] opacity-70 text-[11px]">
        <Chip text={`score ${candidate.s ?? "-"}`} />
        {candidate.source && <Chip text={candidate.source} />}
      </div>
    </div>
  );
}
