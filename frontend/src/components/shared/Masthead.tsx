import type { ReactNode } from "react";
import DecorativeMark from "./DecorativeMark";

interface MastheadProps {
  eyebrow: string;
  title: string;
  markVariant?: 3 | 4;
  children?: ReactNode;
}

export default function Masthead({
  eyebrow,
  title,
  markVariant = 3,
  children,
}: MastheadProps) {
  return (
    <section className="min-h-[196px] grid grid-cols-[1fr_180px] items-end gap-6 border-b-2 border-ink mb-[22px] pb-[22px] max-[820px]:grid-cols-1">
      <div>
        <p className="m-0 mb-3 text-[13px] font-extrabold text-blue uppercase tracking-normal">
          {eyebrow}
        </p>
        <h1 className="m-0 max-w-[820px] text-[clamp(38px,8vw,92px)] leading-[0.94] font-black tracking-normal">
          {title}
        </h1>
        {children}
      </div>
      <div className="max-[820px]:w-[148px] max-[820px]:h-[108px]">
        <DecorativeMark variant={markVariant} />
      </div>
    </section>
  );
}
