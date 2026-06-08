import type { ReactNode } from "react";

interface FieldProps {
  label: string;
  htmlFor?: string;
  children: ReactNode;
}

export default function Field({ label, htmlFor, children }: FieldProps) {
  return (
    <div className="grid gap-2">
      <label htmlFor={htmlFor} className="text-xs font-extrabold text-blue">
        {label}
      </label>
      {children}
    </div>
  );
}
