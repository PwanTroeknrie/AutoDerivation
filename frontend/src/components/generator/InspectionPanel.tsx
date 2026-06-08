import Chip from "../shared/Chip";
import type { RootAnalysis } from "../../types";

interface InspectionPanelProps {
  root: RootAnalysis | null;
}

function sampleText(root: RootAnalysis): string {
  if (!root.sample?.result) return "屈折样例: --";
  return `屈折样例: ${root.sample.result}`;
}

export default function InspectionPanel({ root }: InspectionPanelProps) {
  if (!root) {
    return (
      <div className="grid gap-3 min-h-[170px] place-items-center text-ink/50 text-center">
        输入词根后可查看合法性、变格/变位类型和样例屈折。
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      <div className="text-[48px] leading-none font-black text-blue overflow-wrap-anywhere break-words">
        {root.base}
      </div>
      <div className={root.valid ? "text-blue" : "text-bad underline decoration-blue decoration-[3px]"}>
        {root.valid ? "合法" : "不合法"}
      </div>
      <div className="flex flex-wrap gap-[6px]">
        {[
          `POS ${root.pos}`,
          `Type ${root.inflection ?? "-"}`,
          `Subtype ${root.subtype ?? "-"}`,
          `Score ${root.score}`,
          `Tokens ${root.tokens.join(" ")}`,
        ].map((item, i) => (
          <Chip key={i} text={item} />
        ))}
      </div>
      <p className="m-0">{root.reason}</p>
      <p className="m-0 text-[13px] min-h-[26px] pt-2 border-t border-line">
        {sampleText(root)}
      </p>
      <ul className="m-0 pl-[18px]">
        {(root.diagnostics.length ? root.diagnostics : ["No diagnostics."]).map(
          (item, i) => (
            <li key={i}>{item}</li>
          )
        )}
      </ul>
    </div>
  );
}
