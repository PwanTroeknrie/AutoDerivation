import CandidateCard from "./CandidateCard";
import type { EtymologyCandidate } from "../../types";

interface CandidateGridProps {
  candidates: EtymologyCandidate[];
}

export default function CandidateGrid({ candidates }: CandidateGridProps) {
  if (candidates.length === 0) {
    return (
      <div className="border border-line bg-white p-2">No recall candidates.</div>
    );
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(164px,1fr))] gap-[10px]">
      {candidates.slice(0, 8).map((c, i) => (
        <CandidateCard key={i} candidate={c} />
      ))}
    </div>
  );
}
