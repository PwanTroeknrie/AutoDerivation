interface DecorativeMarkProps {
  variant: 3 | 4;
}

export default function DecorativeMark({ variant }: DecorativeMarkProps) {
  if (variant === 3) {
    return (
      <div className="h-[156px] grid grid-cols-2 grid-rows-2 gap-3" aria-hidden="true">
        <span className="block border-2 border-ink bg-blue" />
        <span className="block border-2 border-ink bg-paper rounded-full" />
        <span className="block border-2 border-ink bg-ink col-span-2" />
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-2 grid-rows-3 gap-[10px] min-h-[260px]"
      aria-hidden="true"
    >
      <span className="block border-2 border-ink bg-blue" />
      <span className="block border-2 border-ink bg-white rounded-full" />
      <span className="block border-2 border-ink bg-white col-span-2" />
      <span className="block border-2 border-ink bg-ink col-span-2" />
    </div>
  );
}
