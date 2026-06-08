import type { CSSProperties } from "react";
import type { WarmupState } from "../../App";

interface WarmupBadgeProps {
  state: WarmupState;
}

const warmupText: Record<WarmupState, string> = {
  warming: "Warming",
  ready: "Ready",
  failed: "Warmup failed",
};

const warmupProgress: Record<WarmupState, string> = {
  warming: "68%",
  ready: "100%",
  failed: "100%",
};

export default function WarmupBadge({ state }: WarmupBadgeProps) {
  return (
    <span
      className="warmup-badge"
      title="Embedding model and ChromaDB warmup"
      aria-live="polite"
      data-state={state}
      style={{ "--warmup-progress": warmupProgress[state] } as CSSProperties}
    >
      <span className="warmup-ring" aria-hidden="true" />
      {warmupText[state]}
    </span>
  );
}
