interface ChipProps {
  text: string;
}

export default function Chip({ text }: ChipProps) {
  return <span className="chip">{text}</span>;
}
