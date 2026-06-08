import { useState, type FormEvent } from "react";
import Field from "../shared/Field";
import Button from "../shared/Button";

interface EtymologistFormProps {
  onSubmit: (concept: string) => Promise<unknown>;
  loading: boolean;
}

export default function EtymologistForm({ onSubmit, loading }: EtymologistFormProps) {
  const [concept, setConcept] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = concept.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="grid grid-cols-[1fr_122px] gap-[10px] items-end max-[920px]:grid-cols-1"
    >
      <Field label="Concept" htmlFor="ety-concept">
        <input
          id="ety-concept"
          value={concept}
          onChange={(event) => setConcept(event.target.value)}
          placeholder="e.g. death, necromancer, harvest"
          className="input-brutal"
        />
      </Field>
      <Button type="submit" disabled={loading}>
        {loading ? "Analyzing" : "Analyze"}
      </Button>
    </form>
  );
}
