import Chip from "../shared/Chip";
import type { RootAnalysis } from "../../types";

interface RootCardProps {
  root: RootAnalysis;
  onClick: (root: RootAnalysis) => void;
}

function sampleText(root: RootAnalysis): string {
  if (!root.sample?.result) return "屈折样例: --";
  return `屈折样例: ${root.sample.result}`;
}

export default function RootCard({ root, onClick }: RootCardProps) {
  return (
    <div
      className="min-h-[142px] grid gap-[10px] content-start p-3 border border-ink glass-strong cursor-pointer"
      tabIndex={0}
      role="button"
      onClick={() => onClick(root)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick(root);
        }
      }}
    >
      <div className="text-[28px] leading-none font-black text-blue break-words">
        {root.base}
      </div>
      <div className="flex flex-wrap gap-[6px]">
        {[root.pos, root.inflection ?? "unknown", root.subtype ?? "-", `${root.score}`].map((item, index) => (
          <Chip key={`${item}-${index}`} text={item} />
        ))}
      </div>
      <div className="min-h-[26px] pt-2 border-t border-line text-[13px]">
        {sampleText(root)}
      </div>
    </div>
  );
}
