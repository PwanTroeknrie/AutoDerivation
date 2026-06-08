import RootCard from "./RootCard";
import type { RootAnalysis } from "../../types";

interface RootGridProps {
  roots: RootAnalysis[];
  onCardClick: (root: RootAnalysis) => void;
}

export default function RootGrid({ roots, onCardClick }: RootGridProps) {
  if (roots.length === 0) {
    return <div className="text-center text-ink/50 py-8">No roots generated yet.</div>;
  }

  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(176px,1fr))] gap-[10px]">
      {roots.map((root, i) => (
        <RootCard key={`${root.base}-${i}`} root={root} onClick={onCardClick} />
      ))}
    </div>
  );
}
