interface PaneHeadProps {
  title: string;
  status?: string;
}

export default function PaneHead({ title, status }: PaneHeadProps) {
  return (
    <div className="h-[34px] flex justify-between items-center border-b border-ink mb-[14px]">
      <h2 className="text-base m-0 tracking-normal">{title}</h2>
      {status !== undefined && (
        <span className="text-xs font-extrabold text-blue">{status}</span>
      )}
    </div>
  );
}
