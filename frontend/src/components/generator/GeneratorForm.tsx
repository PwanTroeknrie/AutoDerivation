import { useState, type FormEvent } from "react";
import Field from "../shared/Field";
import Button from "../shared/Button";
import type { GeneratePayload } from "../../types";

interface GeneratorFormProps {
  onSubmit: (payload: GeneratePayload) => Promise<unknown>;
  loading: boolean;
}

export default function GeneratorForm({ onSubmit, loading }: GeneratorFormProps) {
  const [pos, setPos] = useState<string>("");
  const [count, setCount] = useState(12);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({ pos: pos || null, count });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="panel glass min-h-[104px] grid grid-cols-[1fr_120px_112px] gap-3 items-end p-4 max-[820px]:grid-cols-1"
    >
      <Field label="词性" htmlFor="generator-pos">
        <select
          id="generator-pos"
          value={pos}
          onChange={(e) => setPos(e.target.value)}
          className="input-brutal"
        >
          <option value="">混合</option>
          <option value="noun">名词</option>
          <option value="verb">动词</option>
        </select>
      </Field>
      <Field label="数量" htmlFor="generator-count">
        <input
          id="generator-count"
          type="number"
          min={1}
          max={64}
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
          className="input-brutal"
        />
      </Field>
      <Button type="submit" disabled={loading}>
        {loading ? "生成中" : "生成"}
      </Button>
    </form>
  );
}
